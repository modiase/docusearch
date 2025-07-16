package cmd

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
)

// searchCmd represents the search command
var searchCmd = &cobra.Command{
	Use:   "search [query]",
	Short: "Search for documents using smart search (exact + wildcard prefix)",
	Long: `Search for documents using smart search (exact + wildcard prefix).

Smart search rules:
- Use exact word matching by default
- If query ends with *, use prefix search (e.g., "prog*")
- Use \* to search for literal * (escape the wildcard)

Examples:
  docusearch search "python programming"
  docusearch search "prog*"
  docusearch search "machine learning" --top-k 10`,
	Args: cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		query := args[0]
		topK, _ := cmd.Flags().GetInt("top-k")
		storageFile, _ := cmd.Flags().GetString("storage-file")

		store, err := loadStorage(storageFile, false)
		if err != nil {
			fmt.Printf("Error loading storage: %v\n", err)
			os.Exit(1)
		}

		start := time.Now()
		results := store.SmartSearch(query, topK)
		duration := time.Since(start)

		searchType := getSearchType(query)
		printSearchResults(results, query, searchType, duration)
	},
}

func init() {
	rootCmd.AddCommand(searchCmd)

	searchCmd.Flags().IntP("top-k", "k", 5, "Number of top results to return")
	searchCmd.Flags().StringP("storage-file", "s", "", "Storage file to load")
} 