# B3 Track Renamer
This Python script automates the renaming of B3 track files by adding the artist's name to the file names based on data fetched from the MusicBrainz API. 
It scans a specified directory for subfolders containing `.wav` files and `discid` files, retrieves the track information from MusicBrainz, 
generates a series of Bash commands to rename the files, and then writes these commands to a shell script with a timestamped filename. 

## Why This Script?  
The B3 enforces a fixed folder structure: `artist/album`. 
While this structure works well for standard artist albums, it presents limitations for compilations. 
Compilation albums are placed under a `Various Artists` folder, and the individual track files only retain their titles, resulting in the loss of artist information.  
A common workaround is to manually append the artist name to each track filename, e.g.:  
```sh
mv "Various Artists/CompilationX/01 first track.wav" "Various Artists/CompilationX/01 first track [artist name].wav"
```
However, this process is tedious when dealing with large collections. 
This script automates the task, making it easy to rename compilation tracks efficiently.  

## Reliability  
At the time of this writing, I have tested this script with a reduced collection of about 50 CDs and have not encountered any issues. 
That being said, I certainly haven't anticipated all possible cases.  
I recommend reviewing the generated renaming scripts before applying them to ensure they meet your expectations. 
Additionally, I encourage using filters to apply the script to a limited number of albums at a time rather than running it on the entire collection at once. 
This approach helps catch potential issues early and allows for adjustments if needed.  

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
The B3 cannot run Python directly, so you need to mount its music folder on a machine that supports Python.  
On Debian, I use `sshfs` to mount the folder:  
```sh
sshfs root@<ip>:/media/hdd1/music <local_mount_folder>
```

### Running the Script  
Execute the script with the following options:  
```sh
python mbz_get_artists.py --path <path_to_directory> [--debug [level]] [--filter <pattern>] [--output <output_name>]
```

### Applying the Renaming  
The script will generate a shell script for renaming the files. Before running it, make it executable:  
```sh
chmod +x rename_filter_20250213204946.sh
./rename_filter_20250213204946.sh
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

