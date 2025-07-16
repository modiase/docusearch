# DocuSearch

An in-memory document storage library with TF-IDF search capabilities written in Go.
Experimental library to practice use of various data structures relevant in full-text searching.

## Features

- **In-memory document storage** with fast retrieval
- **Enhanced trie data structure** for efficient prefix searching with document mappings
- **Forward index** mapping documents to word frequencies
- **Smart search** with automatic exact/prefix fallback and wildcard support
- **TF-IDF search** for relevant document retrieval (top-k results)
- **CLI interface** for easy document management and searching
- **REPL with command history** for interactive document management
- **Persistent storage** via JSON files

## Architecture

The library consists of several key components:

1. **Enhanced Trie** (`pkg/trie`): Efficient prefix searching with document mappings stored directly in the trie
2. **Forward Index** (`pkg/index`): Maps documents to word frequencies for TF calculation
3. **Document Storage** (`pkg/storage`): Main class that orchestrates all components
4. **CLI Interface** (`cmd`): Command-line tools for document management using Cobra

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd docusearch

# Install dependencies
go mod tidy

# Build the main application
go build -o docusearch-demo .

# Build the CLI tool
go build -o docusearch ./cmd/docusearch
```

## Usage

### Go Library

```go
package main

import (
    "fmt"
    "docusearch/pkg/storage"
)

func main() {
    // Create storage instance
    store := storage.New()

    // Add documents
    docID := store.AddDocument("Go is a programming language", "go_doc")

    // Search documents
    results := store.Search("programming", 5)
    for _, result := range results {
        fmt.Printf("Document: %s, Score: %.4f\n", result.DocID, result.Score)
    }

    // Prefix search
    words := store.PrefixSearch("prog")
    fmt.Printf("Words starting with 'prog': %v\n", words)
}
```

### Command Line Interface

#### Adding Documents

```bash
# Add a single document from a file
./docusearch add examples/sample_documents.txt

# Add all text files from a directory
./docusearch add examples/

# Add with custom document ID (single files only)
./docusearch add examples/sample_documents.txt --doc-id python_doc

# Save to persistent storage
./docusearch add examples/ --storage-file my_docs.json
```

**Supported file types:** `.txt`, `.md`, `.py`, `.js`, `.html`, `.css`, `.json`, `.xml`, `.csv`, `.tsv`, `.log`, `.rst`, `.tex`, `.adoc`, `.org`, `.go`

#### Searching Documents

```bash
# Smart search (exact + prefix fallback)
./docusearch search "machine learning"

# Prefix search using wildcard
./docusearch search "prog*"

# Search with custom number of results
./docusearch search "python programming" --top-k 10

# Search with persistent storage
./docusearch search "web development" --storage-file my_docs.json
```

**Smart Search Rules:**

- **Exact matching by default**: `search "python"` finds documents containing "python"
- **Wildcard prefix search**: `search "prog*"` finds documents containing words starting with "prog"
- **Escape wildcards**: Use `search "\\*"` to search for literal asterisk

#### Prefix Searching

```bash
# Find words starting with a prefix
./docusearch prefix "prog"

# Output: programming, progressive, etc.
```

#### Interactive REPL

```bash
# Start interactive REPL with command history
./docusearch repl
```

#### Statistics

```bash
# Show storage statistics
./docusearch stats --storage-file docs.json
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
- If query ends with `*`, use prefix search (e.g., "prog\*")
- Use `\\*` to search for literal `*` (escape the wildcard)

## Development

### Running Tests

```bash
# Run all tests
go test ./...

# Run tests with verbose output
go test -v ./...

# Run tests for specific package
go test ./pkg/trie
go test ./pkg/storage
```

### Project Structure

```
docusearch/
├── cmd/                    # CLI commands
│   ├── docusearch/        # CLI binary entry point
│   ├── root.go            # Root command and utilities
│   ├── add.go             # Add command
│   ├── search.go          # Search command
│   ├── prefix.go          # Prefix command
│   ├── stats.go           # Stats command
│   └── repl.go            # REPL command
├── pkg/                   # Core packages
│   ├── trie/              # Trie data structure
│   ├── index/             # Forward/reverse indices
│   └── storage/           # Main document storage
├── examples/              # Example documents
├── main.go                # Demo application
├── go.mod                 # Go module definition
└── README.md              # Documentation
```

### Algorithm Details

#### TF-IDF Scoring

The library implements TF-IDF (Term Frequency-Inverse Document Frequency) scoring:

- **TF (Term Frequency)**: `word_count_in_doc / total_words_in_doc`
- **IDF (Inverse Document Frequency)**: `log2((total_docs + 1) / (docs_containing_word + 1)) + 1`
- **TF-IDF Score**: `TF * IDF`

#### Data Structures

1. **Trie**: Each node stores:

   - Child character mappings
   - End-of-word flag
   - Document set containing the word
   - Word count per document

2. **Forward Index**: Maps document IDs to word frequency maps
3. **Storage**: Orchestrates all components and provides the main API

## Performance Characteristics

- **Space Complexity**: O(W × D) where W is unique words and D is documents
- **Search Time**: O(Q × log(W)) where Q is query terms
- **Prefix Search Time**: O(P + R) where P is prefix length and R is results
- **Insert Time**: O(W) where W is words in document

## License

This project is available under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Comparison with Original Python Implementation

This Go implementation provides complete functionality parity with the original Python version:

- ✅ Same TF-IDF algorithms and scoring
- ✅ Identical CLI interface and commands
- ✅ Same smart search with wildcard support
- ✅ JSON persistence compatibility
- ✅ Comprehensive test coverage
- ✅ REPL with same commands
- ⚡ Improved performance due to Go's efficiency
- 🔧 Better memory management and type safety
