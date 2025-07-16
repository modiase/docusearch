package cmd

import (
	"fmt"
	"os"
	"sort"
	"time"

	"github.com/spf13/cobra"
)

// prefixCmd represents the prefix command
var prefixCmd = &cobra.Command{
	Use:   "prefix [prefix]",
	Short: "Search for words that start with a prefix",
	Long: `Search for words that start with a prefix.

Examples:
  docusearch prefix prog
  docusearch prefix mach`,
	Args: cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		prefix := args[0]
		storageFile, _ := cmd.Flags().GetString("storage-file")

		store, err := loadStorage(storageFile, false)
		if err != nil {
			fmt.Printf("Error loading storage: %v\n", err)
			os.Exit(1)
		}

		start := time.Now()
		words := store.PrefixSearch(prefix)
		duration := time.Since(start)

		if len(words) == 0 {
			fmt.Printf("No words found starting with '%s'\n", prefix)
			fmt.Printf("Prefix search completed in %s seconds\n", formatDuration(duration))
			return
		}

		sort.Strings(words)
		fmt.Printf("Words starting with '%s' (found in %s seconds):\n", prefix, formatDuration(duration))
		for _, word := range words {
			fmt.Printf("  %s\n", word)
		}
	},
}

func init() {
	rootCmd.AddCommand(prefixCmd)

	prefixCmd.Flags().StringP("storage-file", "s", "", "Storage file to load")
} 