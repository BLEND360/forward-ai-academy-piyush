from src.transformers.article_transformer import ArticleTransformer

transformer = ArticleTransformer()
raw_hn = [{"title": "Test", "url": "http://example.com", "time": 1234567890}]
articles = transformer.transform_hackernews(raw_hn)
assert len(articles) == 1
assert articles[0].title == "Test"
print("✅ Transformer works!")
