"""
DocuSearch - In-memory document storage library with TF-IDF search
"""

from .index import ForwardIndex, ReverseIndex
from .storage import DocumentStorage
from .trie import Trie

__version__ = "0.1.0"
__all__ = ["DocumentStorage", "Trie", "ForwardIndex", "ReverseIndex"]
