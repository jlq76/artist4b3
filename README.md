# MusicBrainz Track Renamer for Brennan B3

This Python script automates the renaming of B3 track files by adding the artist's name to the file names based on data fetched from the MusicBrainz API. 
It scans a specified directory for subfolders containing `.wav` files and `discid` files, retrieves the track information from MusicBrainz, 
generates a series of Bash commands to rename the files, and then writes these commands to a shell script with a timestamped filename. 
The script also includes a filter for subfolder names.

## Features
- Scans a specified directory for subfolders containing `.wav` files and `discid` files.
- Queries the MusicBrainz API to fetch track information based on the `discid`.
- Generates a Bash script with commands to rename the track files, adding artist names.
- Adds a timestamp to the script filename to ensure uniqueness.

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/jlq76/artist4b3.git
   
2. Install the required dependencies:
   ```sh
   pip install requests

## Usage
The B3 cannot run python, it is necessary to mount its folder on a machine that can run python.
On debian, I'm using sshfs
```sh
sshfs root@<ip>:/media/hdd1/music .<local_mount>
```

Run the script with the following options:
```sh
python mbz_get_artists.py --path <path_to_directory> [--debug [level]] [--filter <pattern>] [--output <output_name>]
```

### Arguments
  * --path (str): Directory containing the discid file and .wav files or the parent directory (mandatory).
  * --debug (int): Set debug mode. If used alone, debug level = 1. If used with a value, debug level = <value> (optional).
  * --filter (str): Pattern to match subfolder names (e.g., 'techno*CD2') (optional).
  * --output (str): Name tag for the output script file (will be rename_<output>_timestamp.sh) (optional).

## Example
```sh
python rename_tracks.py --path /path/to/music --debug 2 --like techno* --output my_script
```

