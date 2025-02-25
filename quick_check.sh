#!/bin/bash

# Check if a directory parameter is provided, if not display usage
if [ -z "$1" ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

TARGET_DIR="$1"

# Check that the provided path is a directory
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: '$TARGET_DIR' is not a valid directory."
    exit 1
fi

# Iterate over all subdirectories
for dir in "$TARGET_DIR"/*/ ; do
    # Find .wav files in the subdirectory that do NOT contain '[' and '].wav'
    files=$(find "$dir" -type f -name "*.wav" ! -regex ".*/.*\[.*\].wav")
    if [[ -n "$files" ]]; then
        echo -e "\n** ${dir%/} **"  # Print folder name without trailing slash as a  **title**
        echo "$files" | while read -r file; do
            echo "- $(basename "$file")"  # Print file name as an item list
        done
    fi
done

