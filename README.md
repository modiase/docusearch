# DocuSearch

An in-memory document storage library with TF-IDF search capabilities, featuring an enhanced trie for prefix searching and efficient indexing.

## Features

- **In-memory document storage** with fast retrieval
- **Enhanced trie data structure** for efficient prefix searching with document mappings
- **Forward index** mapping documents to word frequencies
- **Smart search** with automatic exact/prefix fallback and wildcard support
- **TF-IDF search** for relevant document retrieval (top-5 results)
- **CLI interface** for easy document management and searching
- **REPL with command history** for interactive document management
- **Persistent storage** via JSON files

## Architecture

The library consists of several key components:

1. **Enhanced Trie**: Efficient prefix searching with document mappings stored directly in the trie
2. **Forward Index**: Maps documents to word frequencies for TF calculation
3. **Document Storage**: Main class that orchestrates all components
4. **CLI Interface**: Command-line tools for document management

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd docusearch

# Install in development mode
pip install -e .
```

## Usage

### Command Line Interface

#### Adding Documents

```bash
# Add a single document from a file
docusearch add examples/sample_documents.txt

# Add all text files from a directory
docusearch add examples/

# Add with custom document ID (single files only)
docusearch add examples/sample_documents.txt --doc-id python_doc
```

**Supported file types:** `.txt`, `.md`, `.py`, `.js`, `.html`, `.css`, `.json`, `.xml`, `.csv`, `.tsv`, `.log`, `.rst`, `.tex`, `.adoc`, `.org`

#### Searching Documents

```bash
# Smart search (exact + prefix fallback)
docusearch search "machine learning"

# Prefix search using wildcard
docusearch search "prog*"

# Search with custom number of results
docusearch search "python programming" --top-k 10

# Search with persistent storage
docusearch search "web development" --storage-file my_docs.json
```

**Smart Search Rules:**

- **Exact matching by default**: `search "python"` finds documents containing "python"
- **Wildcard prefix search**: `search "prog*"` finds documents containing words starting with "prog"
- **Escape wildcards**: Use `search "\\*"` to search for literal asterisk

#### Prefix Searching

```bash
# Find words starting with a prefix
docusearch prefix "prog"

# Output: programming, progressive, etc.
```

#### Interactive REPL

```bash
# Start interactive REPL with command history
uv run repl

# Or use the CLI command
docusearch repl
```

#### Statistics

```bash
# Show storage statistics
docusearch stats --storage-file docs.json
```

### REPL Commands

The REPL supports the following commands:

- `add <path>` - Add a document from a file or all text files from a directory
- `addtext` - Add a document by pasting text (end with blank line)
- `delete <doc_id>` - Delete a document by ID
- `search <query>` - Smart search (exact + wildcard prefix)
- `prefix <prefix>` - List words starting with prefix
- `stats` - Show storage statistics
- `list` - List all document IDs
- `help` - Show help message
- `exit/quit/q` - Exit the REPL

**Smart search rules:**

- Use exact word matching by default
- If query ends with _, use prefix search (e.g., "prog_")
- Use \\_ to search for literal _ (escape the wildcard)

### Programmatic Usage

```python
from docusearch import DocumentStorage

# Create storage instance
storage = DocumentStorage()

# Add documents
doc_id1 = storage.add_document_from_path("examples/sample_documents.txt")  # Single file
doc_ids = storage.add_document_from_path("examples/")  # All files in directory
doc_id2 = storage.add_document("Some text content", "custom_id")

# Search documents (smart search with automatic fallback)
results = storage.smart_search("python programming", top_k=5)
for doc_id, score, preview in results:
    print(f"Document: {doc_id}, Score: {score}")
    print(f"Preview: {preview}")

# Search documents (exact word matching only)
results = storage.search("python programming", top_k=5)
for doc_id, score, preview in results:
    print(f"Document: {doc_id}, Score: {score}")
    print(f"Preview: {preview}")

# Search documents (prefix matching only)
results = storage.search_by_prefix("prog", top_k=5)
for doc_id, score, preview in results:
    print(f"Document: {doc_id}, Score: {score}")
    print(f"Preview: {preview}")

# Prefix search for words
words = storage.prefix_search("prog")
print(f"Words starting with 'prog': {words}")

# Get document info
info = storage.get_document_info(doc_id1)
print(f"Document has {info['total_words']} words")

# Get statistics
stats = storage.get_stats()
print(f"Total documents: {stats['total_documents']}")
```

## Enhanced Trie Features

### Document Mappings

The trie now stores document mappings directly, eliminating the need for a separate reverse index:

- Each word node contains a set of document IDs that contain that word
- Word counts per document are stored for accurate TF-IDF calculation
- Automatic cleanup when documents are removed

### Prefix-Based Document Search

Search for documents containing words that start with a specific prefix:

```bash
# Find documents containing words starting with "prog"
docusearch search-prefix "prog"

# Find documents containing words starting with "py"
docusearch search-prefix "py"
```

### Efficient Document Management

- Words are only removed from the trie when no documents contain them
- Automatic cleanup of empty words during document removal
- Proper handling of document addition and deletion

## TF-IDF Search Algorithm

The search functionality uses TF-IDF (Term Frequency-Inverse Document Frequency) scoring:

- **TF (Term Frequency)**: How often a word appears in a document
- **IDF (Inverse Document Frequency)**: How rare a word is across all documents
- **TF-IDF Score**: TF × IDF, measuring word importance in context

Higher scores indicate more relevant documents for the search query.

## Data Structures

### Enhanced Trie

- Efficient prefix searching in O(m) time where m is prefix length
- Stores document mappings directly in word nodes
- Supports insertion, deletion, and prefix matching
- Automatic cleanup of empty words
- Case-insensitive word storage

### Forward Index

- Maps document IDs to word frequency dictionaries
- Enables fast TF calculation
- Tracks document lengths for normalization

## Performance Characteristics

- **Document Addition**: O(n) where n is number of words
- **Exact Search**: O(k × m) where k is query words and m is documents containing those words
- **Prefix Search**: O(p) where p is prefix length
- **Prefix Document Search**: O(p + d) where p is prefix length and d is documents containing matching words
- **Memory**: O(total_words + total_documents)

## Example Session

```bash
# Add sample documents (single file or directory)
docusearch add examples/sample_documents.txt --storage-file test_docs.json
docusearch add examples/ --storage-file test_docs.json  # Add all files in directory

# Smart search examples
docusearch search "python programming" --storage-file test_docs.json
# Returns documents about Python with high scores

docusearch search "prog*" --storage-file test_docs.json
# Returns documents containing programming, progressive, etc.

docusearch search "web" --storage-file test_docs.json
# Returns documents about web development

# Prefix search for words
docusearch prefix "prog" --storage-file test_docs.json
# Returns: programming, progressive

# View statistics
docusearch stats --storage-file test_docs.json
```

## Requirements

- Python 3.8+
- Click (for CLI)
- pathlib2 (for older Python versions)

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest

# Run linting
flake8 docusearch/
```

## License

MIT License - see LICENSE file for details.
