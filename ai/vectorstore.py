import os
from ai.embeddings import get_embedding_model

class SimpleVectorStore:
    def __init__(self):
        self.documents = []
        self.metadatas = []
        
    def add_texts(self, texts, metadatas=None):
        for i, t in enumerate(texts):
            self.documents.append(t)
            if metadatas:
                self.metadatas.append(metadatas[i])
            else:
                self.metadatas.append({})
                
    def similarity_search(self, query, k=3):
        matches = []
        query_words = query.lower().split()
        for i, doc in enumerate(self.documents):
            score = 0
            doc_lower = doc.lower()
            for word in query_words:
                if word in doc_lower:
                    score += 1
            if score > 0:
                matches.append((doc, self.metadatas[i], score))
                
        matches.sort(key=lambda x: x[2], reverse=True)
        
        # If no keyword matches, just return the first few
        if not matches and self.documents:
            return self.documents[:k]
            
        return [m[0] for m in matches[:k]]

vector_store_instance = SimpleVectorStore()

def get_vectorstore():
    return vector_store_instance
