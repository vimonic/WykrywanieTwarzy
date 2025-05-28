import numpy as np
from numpy.linalg import norm

class FaceMatcher:
    def __init__(self, threshold=0.60):
        self.threshold = threshold

    def cosine_similarity(self, emb1, emb2):
        return np.dot(emb1, emb2) / (norm(emb1) * norm(emb2))

    def match(self, embedding, database_embeddings):
        # database_embeddings: list of (user_id, emb)
        best_score = -1
        best_id = None
        for user_id, db_emb in database_embeddings:
            score = self.cosine_similarity(embedding, db_emb)
            if score > best_score:
                best_score, best_id = score, user_id
        if best_score >= self.threshold:
            return best_id, best_score
        return None, best_score