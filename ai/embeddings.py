class SimpleEmbeddingFunction:
    def __init__(self):
        pass
    def embed_documents(self, texts):
        return [[0.1] * 384 for _ in texts]
    def embed_query(self, text):
        return [0.1] * 384

def get_embedding_model():
    return SimpleEmbeddingFunction()
