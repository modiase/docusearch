# DocuSearch

An in-memory document storage library with TF-IDF search capabilities.
Experimental library to practice use of various data structures relevant in full-text searching.

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
uv sync
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
