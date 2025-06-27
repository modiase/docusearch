from docusearch.cli import PROJECT_DESCRIPTION

from .index import ForwardIndex, ReverseIndex
from .storage import DocumentStorage
from .trie import Trie

__version__ = "0.1.0"
__all__ = ["DocumentStorage", "Trie", "ForwardIndex", "ReverseIndex"]
__doc__ = PROJECT_DESCRIPTION
