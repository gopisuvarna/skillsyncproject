# # """Embedding service using Sentence Transformers. Caches model and vectors."""
# # import logging
# # from typing import List, Union
# # import numpy as np
# # from django.conf import settings

# # """logging for debugging and error tracking,
# # type hints for better code readability and maintenance, 
# # numpy for vector operations, 
# # django settings for read config"""

# # #Creates a logger for this module.
# # logger = logging.getLogger(__name__)

# # #Global variable to cache the model instance. Initialized to None.
# # #_get_model function will load the _model once and reuse for subsequent calls to avoid loading the model multiple times.
# # _model = None

# # #This function loads the model only once. If the model is already loaded, it returns the cached instance.
# # def _get_model():
# #     global _model

# #     #If the model has not been loaded yet.
# #     if _model is None:

# #         #Import the model class.,Reads model name from Django settings.If not specified, defaults to 'all-MiniLM-L6-v2'.
# #         from sentence_transformers import SentenceTransformer
# #         name = settings.EMBEDDING_CONFIG.get('MODEL_NAME', 'all-MiniLM-L6-v2')
# #         #Loads the pretrained embedding model.
# #         _model = SentenceTransformer(name)
# #     return _model

# # '''This is the main function used to convert text → vectors.
# # texts -> list of input texts
# # normalize -> normalize vectors (for cosine similarity)
# # return_numpy -> return numpy array instead of list'''

# # def encode(
# #     texts: List[str],
# #     normalize: bool = False,
# #     return_numpy: bool = False,
# # ) -> Union[List[List[float]], np.ndarray]:
    
# #     """Batch encode texts to vectors."""
# #     if not texts:
# #         if return_numpy:
# #             #If no texts are provided and return_numpy is True, return an empty numpy array with the correct shape.
# #             return np.array([], dtype=np.float32)
# #         return []
# #     #Get the model instance (cached) and encode the texts to vectors. Normalize if specified.
# #     model = _get_model()

# #     vectors = model.encode(
# #         texts,
# #         convert_to_numpy=True,
# #         normalize_embeddings=normalize,
# #     )
# #     #FAISS requires vectors in float32 format.
# #     vectors = np.asarray(vectors, dtype=np.float32)
# #     #If only one text is encoded, the vector might look like:(384,)But FAISS expects:(1, 384) So we expand the dimension.
# #     if vectors.ndim == 1:
# #         vectors = np.expand_dims(vectors, 0)
# #     #Return numpy array if specified, otherwise convert to list of lists.
# #     if return_numpy:
# #         return vectors
# #     return vectors.tolist()

# # #This function encodes one text instead of a list.It uses the encode function but handles the case where the input text is empty by returning a zero vector of the appropriate dimension.
# # def encode_single(text: str, normalize: bool = False) -> List[float]:
# #     """Encode single text."""
# #     if not text:
# #         dim = settings.EMBEDDING_CONFIG.get('DIMENSION', 384)
# #         return [0.0] * dim  #[0, 0, ..., 0] vector of length dim
# #     result = encode([text], normalize=normalize, return_numpy=False) #Convert the text to embedding.
# #     return result[0]  #Return the first (and only) vector from the result list.






# # '''This module implements an embedding service using Sentence Transformers. 
# # It loads the embedding model lazily and caches it globally to avoid repeated loading. 
# # The encode function converts a batch of texts into vector embeddings with optional normalization 
# # for cosine similarity. The vectors are returned either as NumPy arrays or Python lists. 
# # The encode_single function is a helper that encodes a single text and handles empty inputs by 
# # returning a zero vector.'''


# """Embedding service using Sentence Transformers. Caches model and vectors."""
# import logging
# from typing import List, Union

# import numpy as np
# from django.conf import settings

# logger = logging.getLogger(__name__)

# _model = None


# def _get_model():
#     global _model
#     if _model is None:
#         from sentence_transformers import SentenceTransformer
#         name = settings.EMBEDDING_CONFIG.get('MODEL_NAME', 'all-MiniLM-L6-v2')
#         try:
#             _model = SentenceTransformer(name, device="cpu")
#         except (NotImplementedError, RuntimeError, Exception) as e:
#             # Catches: meta tensor errors, device errors, version mismatches
#             # Root cause: PyTorch version too new for sentence-transformers
#             # Fix: pip install torch==2.0.1 sentence-transformers==2.2.2
#             logger.exception("Failed to initialize SentenceTransformer: %s", e)
#             _model = None
#     return _model


# def encode(
#     texts: List[str],
#     normalize: bool = False,
#     return_numpy: bool = False,
# ) -> Union[List[List[float]], np.ndarray]:
#     """Batch encode texts to vectors. Optionally L2-normalize for cosine similarity (e.g. FAISS IndexFlatIP)."""
#     if not texts:
#         if return_numpy:
#             return np.array([], dtype=np.float32)
#         return []
#     model = _get_model()
#     if model is None:
#         # Fallback: return zero vectors with configured dimension to keep pipeline running
#         dim = settings.EMBEDDING_CONFIG.get('DIMENSION', 384)
#         if return_numpy:
#             return np.zeros((len(texts), dim), dtype=np.float32)
#         return [[0.0] * dim for _ in texts]

#     vectors = model.encode(
#         texts,
#         convert_to_numpy=True,
#         normalize_embeddings=normalize,
#     )
#     vectors = np.asarray(vectors, dtype=np.float32)
#     if vectors.ndim == 1:
#         vectors = np.expand_dims(vectors, 0)
#     if return_numpy:
#         return vectors
#     return vectors.tolist()


# def encode_single(text: str, normalize: bool = False) -> List[float]:
#     """Encode single text."""
#     if not text:
#         dim = settings.EMBEDDING_CONFIG.get('DIMENSION', 384)
#         return [0.0] * dim
#     result = encode([text], normalize=normalize, return_numpy=False)
#     return result[0]

"""
Embedding service using Google GenAI (gemini-embedding-001).
Replaces sentence-transformers — no PyTorch, no model download, instant cold start.
Public API is identical: encode() and encode_single() — no other file needs changing.
"""
import logging
from typing import List, Union

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        try:
            from google import genai
            api_key = settings.GOOGLE_AI_API_KEY
            if not api_key:
                raise ValueError("GOOGLE_AI_API_KEY is empty — set it in your .env file")
            _client = genai.Client(api_key=api_key)
            logger.info("Google GenAI embedding client ready")
        except Exception as e:
            logger.exception("Could not create Google GenAI client: %s", e)
            _client = None
    return _client


def _dim() -> int:
    return settings.EMBEDDING_CONFIG.get('DIMENSION', 768)


def _zero(n: int) -> np.ndarray:
    return np.zeros((n, _dim()), dtype=np.float32)


def _call_api(texts: List[str], model: str, task_type: str) -> np.ndarray:
    client = _get_client()
    if client is None:
        return _zero(len(texts))

    # FIX: new google-genai client expects plain name e.g. 'gemini-embedding-001'
    # NOT 'models/gemini-embedding-001' — strip the prefix if someone set it wrong
    clean_model = model.replace('models/', '').strip()

    try:
        all_vectors: List[List[float]] = []

        for i in range(0, len(texts), 100):
            batch = texts[i: i + 100]
            result = client.models.embed_content(
                model=clean_model,
                contents=batch,
                config={"task_type": task_type},
            )
            for emb in result.embeddings:
                all_vectors.append(emb.values)

        arr = np.array(all_vectors, dtype=np.float32)
        if arr.ndim == 1:
            arr = np.expand_dims(arr, 0)
        return arr

    except Exception as e:
        logger.warning("Google embedding API error: %s — returning zero vectors", e)
        return _zero(len(texts))


def encode(
    texts: List[str],
    normalize: bool = False,
    return_numpy: bool = False,
    task_type: str = "SEMANTIC_SIMILARITY",
) -> Union[List[List[float]], np.ndarray]:
    """Batch encode texts to embedding vectors."""
    if not texts:
        return np.array([], dtype=np.float32) if return_numpy else []

    model = settings.EMBEDDING_CONFIG.get('MODEL_NAME', 'gemini-embedding-001')
    vectors = _call_api(texts, model, task_type)

    if normalize and vectors.size > 0:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        vectors = vectors / norms

    return vectors if return_numpy else vectors.tolist()


def encode_single(text: str, normalize: bool = False) -> List[float]:
    """Encode a single string. Returns zero vector if empty or API fails."""
    if not text or not text.strip():
        return [0.0] * _dim()
    result = encode([text], normalize=normalize, return_numpy=False)
    return result[0] if result else [0.0] * _dim()