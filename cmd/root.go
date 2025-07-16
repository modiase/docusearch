package cmd

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"docusearch/pkg/storage"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

const (
	projectDescription = "DocuSearch - a document storage library."
)

var cfgFile string

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "docusearch",
	Short: "Document storage library with TF-IDF search",
	Long:  projectDescription,
	// Uncomment the following line if your bare application
	// has an action associated with it:
	// Run: func(cmd *cobra.Command, args []string) { },
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {
	cobra.OnInitialize(initConfig)

	// Here you will define your flags and configuration settings.
	// Cobra supports persistent flags, which, if defined here,
	// will be global for your application.

	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.docusearch.yaml)")

	// Cobra also supports local flags, which will only run
	// when this action is called directly.
	rootCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

// initConfig reads in config file and ENV variables if set.
func initConfig() {
	if cfgFile != "" {
		// Use config file from the flag.
		viper.SetConfigFile(cfgFile)
	} else {
		// Find home directory.
		home, err := os.UserHomeDir()
		cobra.CheckErr(err)

		// Search config in home directory with name ".docusearch" (without extension).
		viper.AddConfigPath(home)
		viper.SetConfigType("yaml")
		viper.SetConfigName(".docusearch")
	}

	viper.AutomaticEnv() // read in environment variables that match

	// If a config file is found, read it in.
	if err := viper.ReadInConfig(); err == nil {
		fmt.Fprintln(os.Stderr, "Using config file:", viper.ConfigFileUsed())
	}
}

// Helper functions for storage operations

func loadStorage(storageFile string, shouldRaise bool) (*storage.DocumentStorage, error) {
	if storageFile == "" {
		return storage.New(), nil
	}

	if _, err := os.Stat(storageFile); os.IsNotExist(err) {
		if shouldRaise {
			return nil, fmt.Errorf("storage file not found: %s", storageFile)
		}
		fmt.Printf("Storage file not found, creating new storage: %s\n", storageFile)
		return storage.New(), nil
	}

	store, err := storage.Load(storageFile)
	if err != nil {
		if shouldRaise {
			return nil, fmt.Errorf("error loading storage: %v", err)
		}
		fmt.Printf("Error loading storage: %v\n", err)
		return storage.New(), nil
	}

	return store, nil
}

func saveStorage(store *storage.DocumentStorage, storageFile string, shouldRaise bool) error {
	if storageFile == "" {
		return nil
	}

	// Create directory if it doesn't exist
	dir := filepath.Dir(storageFile)
	if err := os.MkdirAll(dir, 0755); err != nil {
		if shouldRaise {
			return fmt.Errorf("error creating directory: %v", err)
		}
		fmt.Printf("Error creating directory: %v\n", err)
		return nil
	}

	if err := store.Save(storageFile); err != nil {
		if shouldRaise {
			return fmt.Errorf("error saving storage: %v", err)
		}
		fmt.Printf("Error saving storage: %v\n", err)
		return nil
	}

	return nil
}

func formatDuration(d time.Duration) string {
	return fmt.Sprintf("%.4f", d.Seconds())
}

func printSearchResults(results []storage.SearchResult, query string, searchType string, duration time.Duration) {
	if len(results) == 0 {
		fmt.Println("No results found.")
		fmt.Printf("Search completed in %s seconds\n", formatDuration(duration))
		return
	}

	fmt.Printf("Found %d results for '%s' (%s) in %s seconds:\n\n", 
		len(results), query, searchType, formatDuration(duration))

	for i, result := range results {
		fmt.Printf("%d. Document: %s\n", i+1, result.DocID)
		fmt.Printf("   Score: %.4f\n", result.Score)
		fmt.Printf("   Preview: %s\n\n", result.Preview)
	}
}

func getSearchType(query string) string {
	if strings.HasSuffix(query, "*") && !strings.HasSuffix(query, "\\*") {
		return "prefix"
	}
	return "exact"
} 