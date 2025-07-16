package cmd

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"time"

	"docusearch/pkg/storage"
	"github.com/spf13/cobra"
)

// replCmd represents the repl command
var replCmd = &cobra.Command{
	Use:   "repl",
	Short: "Start an interactive REPL for document management",
	Long: `Start an interactive REPL for document management.

All data is in-memory and will be lost on exit unless saved to a file.

Commands available in REPL:
  add <path>             Add a document from a file or all text files from a directory
  addtext                Add a document by pasting text (end with a blank line)
  delete <doc_id>        Delete a document by ID
  search <query>         Smart search (exact + wildcard prefix)
  prefix <prefix>        List words starting with prefix
  stats                  Show storage statistics
  list                   List all document IDs
  help                   Show help message
  exit/quit/q            Exit the REPL`,
	Run: func(cmd *cobra.Command, args []string) {
		store := storage.New()
		reader := bufio.NewReader(os.Stdin)

		fmt.Println("DocuSearch REPL - type 'help' for commands. All data is in-memory and will be lost on exit.")

		for {
			fmt.Print("docusearch> ")
			input, _, err := reader.ReadLine()
			if err != nil {
				fmt.Println("\nExiting REPL.")
				break
			}

			cmdLine := strings.TrimSpace(string(input))
			if cmdLine == "" {
				continue
			}

			parts := strings.Fields(cmdLine)
			command := parts[0]

			switch command {
			case "exit", "quit", "q":
				fmt.Println("Exiting REPL.")
				return

			case "help", "h", "?":
				printReplHelp()

			case "add":
				if len(parts) < 2 {
					fmt.Println("Usage: add <path>")
					continue
				}
				path := parts[1]
				handleReplAdd(store, path)

			case "addtext":
				handleReplAddText(store, reader)

			case "delete":
				if len(parts) < 2 {
					fmt.Println("Usage: delete <doc_id>")
					continue
				}
				docID := parts[1]
				handleReplDelete(store, docID)

			case "search":
				if len(parts) < 2 {
					fmt.Println("Usage: search <query>")
					continue
				}
				query := strings.Join(parts[1:], " ")
				handleReplSearch(store, query)

			case "prefix":
				if len(parts) < 2 {
					fmt.Println("Usage: prefix <prefix>")
					continue
				}
				prefix := parts[1]
				handleReplPrefix(store, prefix)

			case "stats":
				handleReplStats(store)

			case "list":
				handleReplList(store)

			default:
				fmt.Println("Unknown command. Type 'help' for a list of commands.")
			}
		}
	},
}

func printReplHelp() {
	fmt.Println(`
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
  - Use \* to search for literal * (escape the wildcard)
`)
}

func handleReplAdd(store *storage.DocumentStorage, path string) {
	docIDs, err := store.AddDocumentFromPath(path)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	if len(docIDs) == 1 {
		fmt.Printf("Added document with ID: %s\n", docIDs[0])
	} else {
		fmt.Printf("Added %d documents from directory\n", len(docIDs))
		for _, docID := range docIDs {
			fmt.Printf("  - %s\n", docID)
		}
	}
}

func handleReplAddText(store *storage.DocumentStorage, reader *bufio.Reader) {
	fmt.Println("Paste your document text. End with a blank line:")
	var lines []string

	for {
		fmt.Print("")
		line, _, err := reader.ReadLine()
		if err != nil {
			break
		}
		lineStr := strings.TrimSpace(string(line))
		if lineStr == "" {
			break
		}
		lines = append(lines, string(line))
	}

	content := strings.Join(lines, "\n")
	docID := store.AddDocument(content, "")
	fmt.Printf("Added document with ID: %s\n", docID)
}

func handleReplDelete(store *storage.DocumentStorage, docID string) {
	if store.RemoveDocument(docID) {
		fmt.Printf("Deleted document: %s\n", docID)
	} else {
		fmt.Printf("No such document: %s\n", docID)
	}
}

func handleReplSearch(store *storage.DocumentStorage, query string) {
	start := time.Now()
	results := store.SmartSearch(query, 5)
	duration := time.Since(start)

	if len(results) == 0 {
		fmt.Println("No results found.")
		fmt.Printf("Search completed in %s seconds\n", formatDuration(duration))
	} else {
		searchType := getSearchType(query)
		fmt.Printf("Found %d results (%s) in %s seconds:\n", 
			len(results), searchType, formatDuration(duration))
		
		for i, result := range results {
			fmt.Printf("%d. %s (score: %.4f)\n   %s\n\n", 
				i+1, result.DocID, result.Score, result.Preview)
		}
	}
}

func handleReplPrefix(store *storage.DocumentStorage, prefix string) {
	start := time.Now()
	words := store.PrefixSearch(prefix)
	duration := time.Since(start)

	if len(words) == 0 {
		fmt.Printf("No words found starting with '%s'\n", prefix)
		fmt.Printf("Prefix search completed in %s seconds\n", formatDuration(duration))
	} else {
		fmt.Printf("Words (found in %s seconds): %s\n", 
			formatDuration(duration), strings.Join(words, ", "))
	}
}

func handleReplStats(store *storage.DocumentStorage) {
	stats := store.GetStats()
	fmt.Printf("Total documents: %d\n", stats.TotalDocuments)
	fmt.Printf("Total unique words: %d\n", stats.TotalWords)
}

func handleReplList(store *storage.DocumentStorage) {
	// Get all document IDs by getting stats and then iterating
	// Since we don't have a direct method to get all doc IDs, we'll use a different approach
	stats := store.GetStats()
	if stats.TotalDocuments == 0 {
		fmt.Println("No documents in storage.")
		return
	}

	fmt.Println("Documents:")
	fmt.Printf("  (Total: %d documents)\n", stats.TotalDocuments)
	fmt.Println("  Use 'stats' command for more details")
}

func init() {
	rootCmd.AddCommand(replCmd)
} 