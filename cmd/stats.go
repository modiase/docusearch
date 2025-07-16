package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

// statsCmd represents the stats command
var statsCmd = &cobra.Command{
	Use:   "stats",
	Short: "Show storage statistics",
	Long: `Show storage statistics including total documents, unique words, and documents in index.

Examples:
  docusearch stats
  docusearch stats --storage-file docs.json`,
	Run: func(cmd *cobra.Command, args []string) {
		storageFile, _ := cmd.Flags().GetString("storage-file")

		store, err := loadStorage(storageFile, false)
		if err != nil {
			fmt.Printf("Error loading storage: %v\n", err)
			os.Exit(1)
		}

		stats := store.GetStats()

		fmt.Println("Storage Statistics:")
		fmt.Printf("  Total documents: %d\n", stats.TotalDocuments)
		fmt.Printf("  Total unique words: %d\n", stats.TotalWords)
		fmt.Printf("  Documents in index: %d\n", stats.TotalDocumentsInIndex)
	},
}

func init() {
	rootCmd.AddCommand(statsCmd)

	statsCmd.Flags().StringP("storage-file", "s", "", "Storage file to load")
} 