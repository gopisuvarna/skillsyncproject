# """Embedding service using Sentence Transformers. Caches model and vectors."""
# import logging
# from typing import List, Union
# import numpy as np
# from django.conf import settings

# """logging for debugging and error tracking,
# type hints for better code readability and maintenance, 
# numpy for vector operations, 
# django settings for read config"""

# #Creates a logger for this module.
# logger = logging.getLogger(__name__)

# #Global variable to cache the model instance. Initialized to None.
# #_get_model function will load the _model once and reuse for subsequent calls to avoid loading the model multiple times.
# _model = None

# #This function loads the model only once. If the model is already loaded, it returns the cached instance.
# def _get_model():
#     global _model

#     #If the model has not been loaded yet.
#     if _model is None:

#         #Import the model class.,Reads model name from Django settings.If not specified, defaults to 'all-MiniLM-L6-v2'.
#         from sentence_transformers import SentenceTransformer
#         name = settings.EMBEDDING_CONFIG.get('MODEL_NAME', 'all-MiniLM-L6-v2')
#         #Loads the pretrained embedding model.
#         _model = SentenceTransformer(name)
#     return _model

# '''This is the main function used to convert text → vectors.
# texts -> list of input texts
# normalize -> normalize vectors (for cosine similarity)
# return_numpy -> return numpy array instead of list'''

# def encode(
#     texts: List[str],
#     normalize: bool = False,
#     return_numpy: bool = False,
# ) -> Union[List[List[float]], np.ndarray]:
    
#     """Batch encode texts to vectors."""
#     if not texts:
#         if return_numpy:
#             #If no texts are provided and return_numpy is True, return an empty numpy array with the correct shape.
#             return np.array([], dtype=np.float32)
#         return []
#     #Get the model instance (cached) and encode the texts to vectors. Normalize if specified.
#     model = _get_model()

#     vectors = model.encode(
#         texts,
#         convert_to_numpy=True,
#         normalize_embeddings=normalize,
#     )
#     #FAISS requires vectors in float32 format.
#     vectors = np.asarray(vectors, dtype=np.float32)
#     #If only one text is encoded, the vector might look like:(384,)But FAISS expects:(1, 384) So we expand the dimension.
#     if vectors.ndim == 1:
#         vectors = np.expand_dims(vectors, 0)
#     #Return numpy array if specified, otherwise convert to list of lists.
#     if return_numpy:
#         return vectors
#     return vectors.tolist()

# #This function encodes one text instead of a list.It uses the encode function but handles the case where the input text is empty by returning a zero vector of the appropriate dimension.
# def encode_single(text: str, normalize: bool = False) -> List[float]:
#     """Encode single text."""
#     if not text:
#         dim = settings.EMBEDDING_CONFIG.get('DIMENSION', 384)
#         return [0.0] * dim  #[0, 0, ..., 0] vector of length dim
#     result = encode([text], normalize=normalize, return_numpy=False) #Convert the text to embedding.
#     return result[0]  #Return the first (and only) vector from the result list.






# '''This module implements an embedding service using Sentence Transformers. 
# It loads the embedding model lazily and caches it globally to avoid repeated loading. 
# The encode function converts a batch of texts into vector embeddings with optional normalization 
# for cosine similarity. The vectors are returned either as NumPy arrays or Python lists. 
# The encode_single function is a helper that encodes a single text and handles empty inputs by 
# returning a zero vector.'''


"""Embedding service using Sentence Transformers. Caches model and vectors."""
import logging
from typing import List, Union

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        name = settings.EMBEDDING_CONFIG.get('MODEL_NAME', 'all-MiniLM-L6-v2')
        try:
            _model = SentenceTransformer(name, device="cpu")
        except (NotImplementedError, RuntimeError, Exception) as e:
            # Catches: meta tensor errors, device errors, version mismatches
            # Root cause: PyTorch version too new for sentence-transformers
            # Fix: pip install torch==2.0.1 sentence-transformers==2.2.2
            logger.exception("Failed to initialize SentenceTransformer: %s", e)
            _model = None
    return _model


def encode(
    texts: List[str],
    normalize: bool = False,
    return_numpy: bool = False,
) -> Union[List[List[float]], np.ndarray]:
    """Batch encode texts to vectors. Optionally L2-normalize for cosine similarity (e.g. FAISS IndexFlatIP)."""
    if not texts:
        if return_numpy:
            return np.array([], dtype=np.float32)
        return []
    model = _get_model()
    if model is None:
        # Fallback: return zero vectors with configured dimension to keep pipeline running
        dim = settings.EMBEDDING_CONFIG.get('DIMENSION', 384)
        if return_numpy:
            return np.zeros((len(texts), dim), dtype=np.float32)
        return [[0.0] * dim for _ in texts]

    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
    )
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim == 1:
        vectors = np.expand_dims(vectors, 0)
    if return_numpy:
        return vectors
    return vectors.tolist()


def encode_single(text: str, normalize: bool = False) -> List[float]:
    """Encode single text."""
    if not text:
        dim = settings.EMBEDDING_CONFIG.get('DIMENSION', 384)
        return [0.0] * dim
    result = encode([text], normalize=normalize, return_numpy=False)
    return result[0]