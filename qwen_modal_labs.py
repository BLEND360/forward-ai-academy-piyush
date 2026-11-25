import json
import aiohttp
import modal

# =========================
# Image
# =========================
# NOTE: B200 (Blackwell SM100) requires CUDA 12.8+.
# The nvidia/cuda:12.8.0-devel base handles this correctly.
# Do NOT use a CUDA 12.4 or older base with B200.
# There is an issue with nccl and dual GPU setups with Blackwell architecture, leading to freezing the initialization of the model after loading nccl, just restart the script.

vllm_image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install(
        "vllm==0.17.0",
        "huggingface-hub==0.36.0",
        "transformers>=4.44.0",
    )
    .run_commands(
        "python -c \"import torch; print(torch.__version__)\"",
        "python -c \"import importlib.metadata as m; print(m.version('nvidia-nccl-cu12'))\""
    )
    .env({
        "HF_XET_HIGH_PERFORMANCE": "1",
        "VLLM_WORKER_MULTIPROC_METHOD": "spawn",
        "NCCL_IB_DISABLE": "1",
        "NCCL_P2P_LEVEL": "NVL",
        "NCCL_CUMEM_ENABLE": "0",
        "NCCL_DEBUG": "WARN",
    })
)
# =========================
# Model config
# =========================

MODEL_NAME = "Qwen/Qwen3.5-27B"
MODEL_REVISION = "main"

# =========================
# Volumes
# =========================

hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

app = modal.App("qwen3_5_27b-openai")

# =========================
# Infra
# =========================

#  B200: 180 GB HBM3e per GPU, 8 TB/s bandwidth, Blackwell architecture.
# Use "B200+" to also allow B300 (Blackwell Ultra) if B200 is unavailable —
# B300 has 288 GB HBM3e and is strictly faster. Both run CUDA 12.8.
#
# Why not H200? The B200 has 2× the memory bandwidth (8 vs 4.8 TB/s),
# which is the primary bottleneck for decode-phase inference.
#
# Why 2 GPUs instead of 1? The 27B model at BF16 is ~54 GB. One B200 holds
# it fine, but 2 GPUs doubles KV cache headroom for long contexts and high
# concurrency, and enables tensor parallelism across NVLink.
#
# Why not 4 or 8? For a 27B model, 2-way TP is the sweet spot. Beyond 2 GPUs
# the all-reduce overhead starts eating into gains for this model size.

N_GPU = 2
MINUTES = 60
VLLM_PORT = 8000

# =========================
# Server
# =========================

@app.function(
    image=vllm_image,
    gpu=f"B200:{N_GPU}",   
    scaledown_window=15 * MINUTES,
    timeout=30* MINUTES,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
@modal.concurrent(max_inputs=64)   # raised: B200 handles more concurrent requests
@modal.web_server(port=VLLM_PORT, startup_timeout=30 * MINUTES)
def serve():
    import subprocess

    cmd = [
        "vllm",
        "serve",
        MODEL_NAME,
        "--revision", MODEL_REVISION,
        "--served-model-name", "qwen3.5-27b",
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),

        # ── Qwen3.5 required ────────────────────────────────────────────────
        "--reasoning-parser", "qwen3",

        # ── Precision ───────────────────────────────────────────────────────
        #  FP8: ~1.5–2× throughput vs BF16 on Blackwell FP8 Tensor Cores.
        # Halves VRAM usage (27B ≈ 27 GB vs 54 GB), leaving ~130 GB per GPU
        # free for KV cache — critical for long contexts and high concurrency.
        # Quality loss is <1-2% on standard benchmarks.
        "--dtype", "bfloat16",          # base weights load in BF16...
        "--quantization", "fp8",        # ...then quantized online to FP8 W8A8

        # ── Context length ──────────────────────────────────────────────────
        #  Raised to 131072 (128K). With FP8 + 2× B200s (360 GB total VRAM
        # minus ~27 GB weights = ~330 GB for KV cache), 128K is very
        # comfortable. Full 262144 is possible but rarely needed for tool use.
        "--max-model-len", "131072",

        # ── CUDA Graphs (CRITICAL) ───────────────────────────────────────────
        #  No --enforce-eager: enables CUDA graph capture on Blackwell.
        # On B200, FlashAttention 4 is the default backend (new in vLLM 0.17),
        # which already has Blackwell-native kernels — no extra flags needed.
        "--max-cudagraph-capture-size", "2048",  # large capture = fewer fallbacks

        # ── Batching & throughput ────────────────────────────────────────────
        "--enable-chunked-prefill",
        "--max-num-batched-tokens", "131072",    # match max-model-len
        "--max-num-seqs", "256",                 # max concurrent sequences

        # ── Memory ──────────────────────────────────────────────────────────
        "--gpu-memory-utilization", "0.92",      # slightly higher on B200: stable

        # ── Multi-GPU ───────────────────────────────────────────────────────
        "--tensor-parallel-size", str(N_GPU),

        # ── Tool calling (keep as requested) ────────────────────────────────
        "--enable-auto-tool-choice",
        "--tool-call-parser", "qwen3_coder",

        # ── Misc ─────────────────────────────────────────────────────────────
        "--max-cudagraph-capture-size", "2048",
    ]

    print("Running command:")
    print(" ".join(cmd))

    subprocess.Popen(" ".join(cmd), shell=True)


# =========================
# Test
# =========================

@app.local_entrypoint()
async def test(test_timeout=10 * MINUTES, content=None, twice=True):
    url = serve.get_web_url()

    system_prompt = {
        "role": "system",
        "content": "You are a helpful AI assistant.",
    }

    if content is None:
        content = "Explain transformers in simple terms."

    messages = [
        system_prompt,
        {"role": "user", "content": content},
    ]

    async with aiohttp.ClientSession(base_url=url) as session:
        print(f"Health check: {url}")
        async with session.get("/health", timeout=test_timeout) as resp:
            assert resp.status == 200

        print("Sending request...")
        await _send_request(session, "qwen3.5-27b", messages)

        if twice:
            messages[1]["content"] = "What makes Qwen different from Llama?"
            await _send_request(session, "qwen3.5-27b", messages)


async def _send_request(session, model: str, messages: list):
    payload = {
        "messages": messages,
        "model": model,
        "stream": True,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    async with session.post(
        "/v1/chat/completions", json=payload, headers=headers
    ) as resp:
        async for raw in resp.content:
            resp.raise_for_status()

            line = raw.decode().strip()
            if not line or line == "data: [DONE]":
                continue

            if line.startswith("data: "):
                line = line[len("data: "):]

            chunk = json.loads(line)
            print(chunk["choices"][0]["delta"].get("content", ""), end="")
    print()