"""
Command-line interface for DocuSearch
"""

import contextlib
import readline
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Final, Optional, ParamSpec, TypeVar

import click

from .storage import DocumentStorage

HISTORY_FILE: Final = Path(".docusearch_history")
DEFAULT_HISTORY_LENGTH: Final = 1000

PROJECT_DESCRIPTION: Final = """
DocuSearch - a document storage library.
"""


P, R = ParamSpec("P"), TypeVar("R")


def docstring(docstring: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to add a docstring to a function."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        func.__doc__ = docstring
        return func

    return decorator


def setup_readline() -> None:
    """Setup readline for command history"""
    readline.set_history_length(DEFAULT_HISTORY_LENGTH)

    if HISTORY_FILE.exists():
        with contextlib.suppress(Exception):
            readline.read_history_file(HISTORY_FILE)
    readline.parse_and_bind("tab: complete")


def save_history() -> None:
    """Save command history to file"""
    with contextlib.suppress(Exception):
        readline.write_history_file(HISTORY_FILE)


@contextlib.contextmanager
def stopwatch() -> Iterator[Callable[[], float]]:
    """Stopwatch context manager"""
    start_time = time.time()
    yield lambda: time.time() - start_time


@click.group()
@click.version_option()
@docstring(PROJECT_DESCRIPTION)
def main() -> None:
    pass


@main.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--doc-id", "-i", help="Custom document ID (only for single files)")
@click.option(
    "--storage-file", "-s", type=click.Path(), help="Storage file to load/save"
)
def add(file_path: Path, doc_id: Optional[str], storage_file: Optional[Path]) -> None:
    """Add a document from a file path or all files in a directory"""
    storage = load_storage(storage_file, raises=False)

    try:
        if file_path.is_file():
            if doc_id:
                content = storage._doc_id_to_document.get(str(file_path), "")
                if not content:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        with open(file_path, "r", encoding="latin-1") as f:
                            content = f.read()

                doc_id = storage.add_document(content, doc_id)
                click.echo(f"Document added with ID: {doc_id}")
            else:
                doc_ids = storage.add_document_from_path(str(file_path))
                click.echo(f"Document added with ID: {doc_ids[0]}")
        elif file_path.is_dir():
            if doc_id:
                click.echo(
                    "Warning: --doc-id option is ignored when adding a directory"
                )

            doc_ids = storage.add_document_from_path(str(file_path))
            click.echo(f"Added {len(doc_ids)} documents from directory")
            for doc_id in doc_ids:
                click.echo(f"  - {doc_id}")
        else:
            click.echo(f"Path is neither a file nor directory: {file_path}", err=True)
            raise click.Abort()

        if storage_file is not None:
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
def search(query: str, top_k: int, storage_file: Optional[Path]) -> None:
    """Search for documents using smart search (exact + wildcard prefix)

    Smart search rules:
    - Use exact word matching by default
    - If query ends with *, use prefix search (e.g., "prog*")
    - Use \\* to search for literal * (escape the wildcard)
    """
    storage = load_storage(storage_file, raises=False)

    with stopwatch() as now:
        results = storage.smart_search(query, top_k)

        if not results:
            click.echo("No results found.")
            click.echo(f"Search completed in {now():.4f} seconds")
            return

        search_type = "exact"
        if query.endswith("*") and not query.endswith("\\*"):
            search_type = "prefix"

        click.echo(
            f"Found {len(results)} results for '{query}' ({search_type}) in {now():.4f} seconds:\n"
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
    storage = load_storage(storage_file, raises=False)

    with stopwatch() as now:
        words = storage.prefix_search(prefix)

        if not words:
            click.echo(f"No words found starting with '{prefix}'")
            click.echo(f"Prefix search completed in {now():.4f} seconds")
            return

        click.echo(f"Words starting with '{prefix}' (found in {now():.4f} seconds):")
        for word in sorted(words):
            click.echo(f"  {word}")


@main.command()
@click.argument("file_path", type=click.Path(path_type=Path))
@click.option("--storage-file", "-s", type=click.Path(), help="Storage file to save to")
def add_and_search(file_path: Path, storage_file: Optional[Path]) -> None:
    """Add a document and then start an interactive search session"""
    storage = load_storage(storage_file, raises=False)

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

    if storage_file is not None:
        save_storage(storage, storage_file, raises=False)

    click.echo("\nStarting interactive search session (type 'quit' to exit):")

    while True:
        # TODO: Use prompt_toolkit for better input handling
        try:
            query = click.prompt("Search query")
            if query.lower() in ["quit", "exit", "q"]:
                break

            with stopwatch() as now:
                results = storage.smart_search(query, 5)

                if not results:
                    click.echo("No results found.")
                    click.echo(f"Search completed in {now():.4f} seconds")
                    continue

                search_type = "exact"
                if query.endswith("*") and not query.endswith("\\*"):
                    search_type = "prefix"

                click.echo(
                    f"\nFound {len(results)} results ({search_type}) in {now():.4f} seconds:"
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
    storage = load_storage(storage_file, raises=False)

    stats = storage.get_stats()

    click.echo("Storage Statistics:")
    click.echo(f"  Total documents: {stats['total_documents']}")
    click.echo(f"  Total unique words: {stats['total_words']}")
    click.echo(f"  Documents in index: {stats['total_documents_in_index']}")


@main.command()
def repl():
    """Start an interactive REPL for document management"""
    setup_readline()

    storage = DocumentStorage()
    click.echo(
        "DocuSearch REPL - type 'help' for commands. All data is in-memory and will be lost on exit."
    )

    while True:
        try:
            cmd = click.prompt("docusearch> ", prompt_suffix="").strip()
            if not cmd:
                continue
            if cmd in {"exit", "quit", "q"}:
                click.echo("Exiting REPL.")
                break
            elif cmd in {"help", "h", "?"}:
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
                with stopwatch() as now:
                    results = storage.smart_search(query.strip(), top_k=5)

                    if not results:
                        click.echo("No results found.")
                        click.echo(f"Search completed in {now():.4f} seconds")
                    else:
                        search_type = "exact"
                        if query.strip().endswith("*") and not query.strip().endswith(
                            "\\*"
                        ):
                            search_type = "prefix"

                        click.echo(
                            f"Found {len(results)} results ({search_type}) in {now():.4f} seconds:"
                        )
                        for i, (doc_id, score, preview) in enumerate(results, 1):
                            click.echo(
                                f"{i}. {doc_id} (score: {score:.4f})\n   {preview}\n"
                            )
            elif cmd.startswith("prefix "):
                _, prefix = cmd.split(" ", 1)
                with stopwatch() as now:
                    words = storage.prefix_search(prefix.strip())

                    if not words:
                        click.echo(f"No words found starting with '{prefix.strip()}'")
                        click.echo(f"Prefix search completed in {now():.4f} seconds")
                    else:
                        click.echo(
                            f"Words (found in {now():.4f} seconds): {', '.join(sorted(words))}"
                        )
            elif cmd == "stats":
                stats = storage.get_stats()
                click.echo(f"Total documents: {stats['total_documents']}")
                click.echo(f"Total unique words: {stats['total_words']}")
            elif cmd == "list":
                doc_ids = list(storage._doc_id_to_document.keys())
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

    save_history()


def save_storage(
    storage: DocumentStorage, file_path: Path, raises: bool = True
) -> None:
    """Save storage to a JSON file"""
    try:
        storage.save(file_path)
    except Exception as e:
        if raises:
            raise
        click.echo(f"Error saving storage: {e}", err=True)


def load_storage(file_path: Path, raises: bool = True) -> DocumentStorage:
    """Load storage from a JSON file"""
    try:
        storage = DocumentStorage.load(file_path)

    except Exception as e:
        click.echo(f"Error loading storage: {e}", err=True)
        if raises:
            raise
        return DocumentStorage()
    else:
        return storage


if __name__ == "__main__":
    main()
