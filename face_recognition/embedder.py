import numpy as np
from keras_facenet import FaceNet

class FaceEmbedder:
    def __init__(self):
        self.embedder = FaceNet()

    def get_embedding(self, preprocessed_face):
        # preprocessed_face: uint8 RGB, shape (1,160,160,3)
        face = preprocessed_face[0]  # (160,160,3)
        emb = self.embedder.embeddings([face])[0]
        # L2‑normalizacja
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb