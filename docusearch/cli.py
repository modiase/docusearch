"""
Command-line interface for DocuSearch
"""

import json
import os
import readline
import time
from pathlib import Path
from typing import Optional

import click

from .storage import DocumentStorage

# History file path
HISTORY_FILE = ".docusearch_history"


def setup_readline():
    """Setup readline for command history"""
    # Set history file
    readline.set_history_length(1000)

    # Try to load existing history
    if os.path.exists(HISTORY_FILE):
        try:
            readline.read_history_file(HISTORY_FILE)
        except Exception:
            pass

    # Set up completion (optional - could be enhanced later)
    readline.parse_and_bind("tab: complete")


def save_history():
    """Save command history to file"""
    try:
        readline.write_history_file(HISTORY_FILE)
    except Exception:
        pass


@click.group()
@click.version_option()
def main():
    """DocuSearch - In-memory document storage with TF-IDF search"""
    pass


@main.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--doc-id", "-i", help="Custom document ID (only for single files)")
@click.option(
    "--storage-file", "-s", type=click.Path(), help="Storage file to load/save"
)
def add(file_path: Path, doc_id: Optional[str], storage_file: Optional[str]):
    """Add a document from a file path or all files in a directory"""
    storage = DocumentStorage()

    # Load existing storage if file provided
    if storage_file and Path(storage_file).exists():
        try:
            storage = load_storage(storage_file)
            click.echo(f"Loaded existing storage from {storage_file}")
        except Exception as e:
            click.echo(f"Error loading storage: {e}", err=True)
            raise click.Abort()

    try:
        if file_path.is_file():
            # Single file
            if doc_id:
                # Use custom document ID for single file
                content = storage.documents.get(str(file_path), "")
                if not content:
                    # Read file content
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        with open(file_path, "r", encoding="latin-1") as f:
                            content = f.read()

                doc_id = storage.add_document(content, doc_id)
                click.echo(f"Document added with ID: {doc_id}")
            else:
                # Use default behavior
                doc_ids = storage.add_document_from_path(str(file_path))
                click.echo(f"Document added with ID: {doc_ids[0]}")
        else:
            # Directory
            if doc_id:
                click.echo(
                    "Warning: --doc-id option is ignored when adding a directory"
                )

            doc_ids = storage.add_document_from_path(str(file_path))
            click.echo(f"Added {len(doc_ids)} documents from directory")
            for doc_id in doc_ids:
                click.echo(f"  - {doc_id}")

        # Save storage if file provided
        if storage_file:
            try:
                save_storage(storage, storage_file)
                click.echo(f"Storage saved to {storage_file}")
            except Exception as e:
                click.echo(f"Error saving storage: {e}", err=True)

    except Exception as e:
        click.echo(f"Error adding document(s): {e}", err=True)
        raise click.Abort()


@main.command()
@click.argument("query")
@click.option("--top-k", "-k", default=5, help="Number of top results to return")
@click.option(
    "--storage-file", "-s", type=click.Path(), help="Storage file to load/save"
)
def search(query: str, top_k: int, storage_file: Optional[str]):
    """Search for documents using smart search (exact + wildcard prefix)

    Smart search rules:
    - Use exact word matching by default
    - If query ends with *, use prefix search (e.g., "prog*")
    - Use \\* to search for literal * (escape the wildcard)
    """
    storage = DocumentStorage()

    # Load storage if file provided
    if storage_file and Path(storage_file).exists():
        try:
            storage = load_storage(storage_file)
        except Exception as e:
            click.echo(f"Error loading storage: {e}", err=True)
            raise click.Abort()

    # Time the search
    start_time = time.time()
    results = storage.smart_search(query, top_k)
    search_time = time.time() - start_time

    if not results:
        click.echo("No results found.")
        click.echo(f"Search completed in {search_time:.4f} seconds")
        return

    # Determine search type for display
    search_type = "exact"
    if query.endswith("*") and not query.endswith("\\*"):
        search_type = "prefix"

    click.echo(
        f"Found {len(results)} results for '{query}' ({search_type}) in {search_time:.4f} seconds:\n"
    )

    for i, (doc_id, score, preview) in enumerate(results, 1):
        click.echo(f"{i}. Document: {doc_id}")
        click.echo(f"   Score: {score:.4f}")
        click.echo(f"   Preview: {preview}")
        click.echo()


@main.command()
@click.argument("prefix")
@click.option("--storage-file", "-s", type=click.Path(), help="Storage file to load")
def prefix(prefix: str, storage_file: Optional[str]):
    """Search for words that start with a prefix"""
    storage = DocumentStorage()

    # Load storage if file provided
    if storage_file and Path(storage_file).exists():
        try:
            storage = load_storage(storage_file)
        except Exception as e:
            click.echo(f"Error loading storage: {e}", err=True)
            raise click.Abort()

    # Time the prefix search
    start_time = time.time()
    words = storage.prefix_search(prefix)
    search_time = time.time() - start_time

    if not words:
        click.echo(f"No words found starting with '{prefix}'")
        click.echo(f"Prefix search completed in {search_time:.4f} seconds")
        return

    click.echo(f"Words starting with '{prefix}' (found in {search_time:.4f} seconds):")
    for word in sorted(words):
        click.echo(f"  {word}")


@main.command()
@click.argument("file_path", type=click.Path(path_type=Path))
@click.option("--storage-file", "-s", type=click.Path(), help="Storage file to save to")
def add_and_search(file_path: Path, storage_file: Optional[str]):
    """Add a document and then start an interactive search session"""
    storage = DocumentStorage()

    # Load existing storage if file provided
    if storage_file and Path(storage_file).exists():
        try:
            storage = load_storage(storage_file)
        except Exception as e:
            click.echo(f"Error loading storage: {e}", err=True)
            raise click.Abort()

    # Add the document
    try:
        doc_ids = storage.add_document_from_path(str(file_path))
        if len(doc_ids) == 1:
            click.echo(f"Document added with ID: {doc_ids[0]}")
        else:
            click.echo(f"Added {len(doc_ids)} documents from directory")
            for doc_id in doc_ids:
                click.echo(f"  - {doc_id}")
    except Exception as e:
        click.echo(f"Error adding document: {e}", err=True)
        raise click.Abort()

    # Save storage if file provided
    if storage_file:
        try:
            save_storage(storage, storage_file)
            click.echo(f"Storage saved to {storage_file}")
        except Exception as e:
            click.echo(f"Error saving storage: {e}", err=True)

    # Start interactive search
    click.echo("\nStarting interactive search session (type 'quit' to exit):")

    while True:
        try:
            query = click.prompt("Search query")
            if query.lower() in ["quit", "exit", "q"]:
                break

            # Time the search
            start_time = time.time()
            results = storage.smart_search(query, 5)
            search_time = time.time() - start_time

            if not results:
                click.echo("No results found.")
                click.echo(f"Search completed in {search_time:.4f} seconds")
                continue

            # Determine search type for display
            search_type = "exact"
            if query.endswith("*") and not query.endswith("\\*"):
                search_type = "prefix"

            click.echo(
                f"\nFound {len(results)} results ({search_type}) in {search_time:.4f} seconds:"
            )
            for i, (doc_id, score, preview) in enumerate(results, 1):
                click.echo(f"{i}. {doc_id} (score: {score:.4f})")
                click.echo(f"   {preview}")
                click.echo()

        except KeyboardInterrupt:
            break
        except Exception as e:
            click.echo(f"Error: {e}")


@main.command()
@click.option("--storage-file", "-s", type=click.Path(), help="Storage file to load")
def stats(storage_file: Optional[str]):
    """Show storage statistics"""
    storage = DocumentStorage()

    # Load storage if file provided
    if storage_file and Path(storage_file).exists():
        try:
            storage = load_storage(storage_file)
        except Exception as e:
            click.echo(f"Error loading storage: {e}", err=True)
            raise click.Abort()

    stats = storage.get_stats()

    click.echo("Storage Statistics:")
    click.echo(f"  Total documents: {stats['total_documents']}")
    click.echo(f"  Total unique words: {stats['total_words']}")
    click.echo(f"  Documents in index: {stats['total_documents_in_index']}")


@main.command()
def repl():
    """Start an interactive REPL for document management"""
    # Setup readline for command history
    setup_readline()

    storage = DocumentStorage()
    click.echo(
        "DocuSearch REPL - type 'help' for commands. All data is in-memory and will be lost on exit."
    )
    click.echo("Use ↑/↓ arrows to navigate command history.")

    while True:
        try:
            cmd = click.prompt("docusearch> ", prompt_suffix="").strip()
            if not cmd:
                continue
            if cmd in {"exit", "quit", "q"}:
                click.echo("Exiting REPL.")
                break
            elif cmd == "help":
                click.echo("""
Commands:
  add <path>             Add a document from a file or all text files from a directory
  addtext                Add a document by pasting text (end with a blank line)
  delete <doc_id>        Delete a document by ID
  search <query>         Smart search (exact + wildcard prefix)
  prefix <prefix>        List words starting with prefix
  stats                  Show storage statistics
  list                   List all document IDs
  help                   Show this help message
  exit/quit/q            Exit the REPL

Smart search rules:
  - Use exact word matching by default
  - If query ends with *, use prefix search (e.g., "prog*")
  - Use \\* to search for literal * (escape the wildcard)
""")
            elif cmd.startswith("add "):
                _, path = cmd.split(" ", 1)
                try:
                    doc_ids = storage.add_document_from_path(path.strip())
                    if len(doc_ids) == 1:
                        click.echo(f"Added document with ID: {doc_ids[0]}")
                    else:
                        click.echo(f"Added {len(doc_ids)} documents from directory")
                        for doc_id in doc_ids:
                            click.echo(f"  - {doc_id}")
                except Exception as e:
                    click.echo(f"Error: {e}")
            elif cmd == "addtext":
                click.echo("Paste your document text. End with a blank line:")
                lines = []
                while True:
                    line = click.prompt("")
                    if not line.strip():
                        break
                    lines.append(line)
                content = "\n".join(lines)
                doc_id = storage.add_document(content)
                click.echo(f"Added document with ID: {doc_id}")
            elif cmd.startswith("delete "):
                _, doc_id = cmd.split(" ", 1)
                if storage.remove_document(doc_id.strip()):
                    click.echo(f"Deleted document: {doc_id.strip()}")
                else:
                    click.echo(f"No such document: {doc_id.strip()}")
            elif cmd.startswith("search "):
                _, query = cmd.split(" ", 1)
                # Time the search
                start_time = time.time()
                results = storage.smart_search(query.strip(), top_k=5)
                search_time = time.time() - start_time

                if not results:
                    click.echo("No results found.")
                    click.echo(f"Search completed in {search_time:.4f} seconds")
                else:
                    # Determine search type for display
                    search_type = "exact"
                    if query.strip().endswith("*") and not query.strip().endswith(
                        "\\*"
                    ):
                        search_type = "prefix"

                    click.echo(
                        f"Found {len(results)} results ({search_type}) in {search_time:.4f} seconds:"
                    )
                    for i, (doc_id, score, preview) in enumerate(results, 1):
                        click.echo(
                            f"{i}. {doc_id} (score: {score:.4f})\n   {preview}\n"
                        )
            elif cmd.startswith("prefix "):
                _, prefix = cmd.split(" ", 1)
                # Time the prefix search
                start_time = time.time()
                words = storage.prefix_search(prefix.strip())
                search_time = time.time() - start_time

                if not words:
                    click.echo(f"No words found starting with '{prefix.strip()}'")
                    click.echo(f"Prefix search completed in {search_time:.4f} seconds")
                else:
                    click.echo(
                        f"Words (found in {search_time:.4f} seconds): {', '.join(sorted(words))}"
                    )
            elif cmd == "stats":
                stats = storage.get_stats()
                click.echo(f"Total documents: {stats['total_documents']}")
                click.echo(f"Total unique words: {stats['total_words']}")
            elif cmd == "list":
                doc_ids = list(storage.documents.keys())
                if not doc_ids:
                    click.echo("No documents in storage.")
                else:
                    click.echo("Documents:")
                    for doc_id in doc_ids:
                        click.echo(f"  {doc_id}")
            else:
                click.echo("Unknown command. Type 'help' for a list of commands.")
        except (KeyboardInterrupt, EOFError):
            click.echo("\nExiting REPL.")
            break

    # Save command history before exiting
    save_history()


def save_storage(storage: DocumentStorage, file_path: str) -> None:
    """Save storage to a JSON file"""
    # Note: We can't easily serialize the trie with document mappings
    # So we'll save the basic data and rebuild the trie on load
    data = {
        "documents": storage.documents,
        "doc_counter": storage.doc_counter,
        "total_documents": storage.total_documents,
        "forward_index": {
            "documents": storage.forward_index.documents,
            "doc_lengths": storage.forward_index.doc_lengths,
        },
    }

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def load_storage(file_path: str) -> DocumentStorage:
    """Load storage from a JSON file"""
    with open(file_path, "r") as f:
        data = json.load(f)

    storage = DocumentStorage()

    # Restore documents
    storage.documents = data["documents"]
    storage.doc_counter = data["doc_counter"]
    storage.total_documents = data.get("total_documents", len(data["documents"]))

    # Restore forward index
    storage.forward_index.documents = data["forward_index"]["documents"]
    storage.forward_index.doc_lengths = data["forward_index"]["doc_lengths"]

    # Rebuild trie with document mappings
    for doc_id, word_counts in storage.forward_index.documents.items():
        for word, count in word_counts.items():
            # Insert word if not already present
            if not storage.trie.search(word):
                storage.trie.insert(word)
            # Add document to word's document set
            storage.trie.add_document_to_word(word, doc_id, count)

    return storage


if __name__ == "__main__":
    main()
