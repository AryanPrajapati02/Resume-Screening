from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Optional


class SemanticEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        return self.model.encode(texts, normalize_embeddings=normalize)

    def compute_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        return float(np.dot(embedding1, embedding2))


def get_semantic_similarity(
    text1: str, text2: str, embedder: Optional[SemanticEmbedder] = None
) -> float:
    if embedder is None:  # type: ignore
        embedder = SemanticEmbedder()
    emb1 = embedder.encode([text1])[0]
    emb2 = embedder.encode([text2])[0]
    return embedder.compute_similarity(emb1, emb2)
