# MusicBrainz Track Renamer

This Python script automates the renaming of B3 track files by adding the artist's name to the file names based on data fetched from the MusicBrainz API. 
It scans a specified directory for subfolders containing `.wav` files and `discid` files, retrieves the track information from MusicBrainz, 
generates a series of Bash commands to rename the files, and then writes these commands to a shell script with a timestamped filename. 
The script also includes a filter for subfolder names.

## Features
- Scans a specified directory for subfolders containing `.wav` files and `discid` files.
- Queries the MusicBrainz API to fetch track information based on the `discid`.
- Generates a Bash script with commands to rename the track files, adding artist names.
- Adds a timestamp to the script filename to ensure uniqueness.

## Warning
Work in progress: the documentation is not yet ready

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/jlq76/artist4b3.git
   
