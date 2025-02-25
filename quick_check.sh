#!/bin/bash

# Iterate over all subdirectories
for dir in */ ; do
    # Find .wav files in the subdirectory that do NOT contain '[' and ']'
    # files=$(find "$dir" -type f -name "*.wav" ! -name "*[*]*")
    files=$(find "$dir" -type f -name "*.wav" ! -regex ".*/.*\[.*\].wav")
    if [[ -n "$files" ]]; then
        echo -e "\n** ${dir%/} **"  # Print folder name without trailing slash
        echo "$files" | while read -r file; do
            echo "- $(basename "$file")"  # Print file name only
        done
    fi
done

