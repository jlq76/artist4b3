from datetime import datetime
import os
import requests
import re
import argparse
import fnmatch


# Define debug level as a global variable
global_debug_level = 0

# Parse arguments
# Mandatory: --path of the folder to scan
# Optional:  --debug level (if empty, level=1)
# Optional:  --like filter of the folder to keep (e.g. Techno*)
def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate a script to rename B3 track files adding artist name based on MusicBrainz data.')
    parser.add_argument('--path', help='Directory containing the discid file and .wav files ot the parent directory')
    parser.add_argument("--debug", nargs='?', const=1, type=int, help="Set debug mode. If used alone, debug level=1. If used with a value, debug level=<value>.")
    parser.add_argument("--like", required=False, help="Pattern to match subfolder names (e.g., 'techno*CD2').")
    parser.add_argument("--output", help="Name tag for the output script file (will be rename_<output>_timestamp.sh).")
    return parser.parse_args()

# Debug print function
def debug_print(message_level, message):
    global global_debug_level
    if global_debug_level >= message_level:
        print(message)

# remove any illegal characters from a string intended to be a filename
def sanitize_filename(filename):
    pattern = r'[<>:"/\\|?*]'
    sanitized_filename = re.sub(pattern, '_', filename)
    return sanitized_filename

# scan the directory given as a parameter
# parameters:
# - directory, mandatory: the path of the folder to scan
# - folder_like, optional: a name filter of the subfolders to keep
def check_directory(directory, folder_like):
    global global_debug_level
    if not os.path.exists(directory):
        print(f"Error: Path '{directory}' does not exist.")
        exit(1)

    #list of albums to be created
    albums = []

    #scan the folders within the current directory (that match the pattern if specified)
    subfolders = [f.path for f in os.scandir(directory) if f.is_dir() and (not folder_like or fnmatch.fnmatch(f.name, folder_like))]
    subfolders.sort()
    
    if subfolders:
        for subfolder in subfolders:
            debug_print(3, f"Checking subfolder: {subfolder}")
            discid_path, wav_files = check_files(subfolder)
            if discid_path and wav_files:
                albums.append((subfolder, len(wav_files), discid_path))
    else:
        discid_path, wav_files = check_files(directory)
        if discid_path and wav_files:
            albums.append((directory, len(wav_files), discid_path))
    
    return albums

# Check a given folder to extract the disc_id and count the number of wav files
def check_files(folder):
    discid_path = os.path.join(folder, 'discid')
    wav_files = [f for f in os.listdir(folder) if f.endswith('.wav')]
    wav_files.sort()
    return (discid_path if os.path.isfile(discid_path) else None, wav_files)

# For a given album, using its disc_id, query the Musicbrainz API to get the track list
def get_album_data(albums):
    global global_debug_level
    album_entries = []
    for folder, wav_count, discid_path in albums:
        with open(discid_path, "r") as file:
            disc_id = file.readline().strip()
        url = f"https://musicbrainz.org/ws/2/discid/{disc_id}?fmt=json&inc=recordings+artist-credits"
        debug_print(2, f"\n---- [ {folder} ] ---- \n >  {wav_count} .wav files, disc_id: {disc_id} \n >  Calling URL: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            tracks = parse_response(response, disc_id, folder)
            if tracks:
                album_entries.append(((folder, wav_count, disc_id), tracks))
            else:
                debug_print(2, f" >  ERROR: failed to retrieve data !")
        else:
            debug_print(2,f" >  Response Status Code: {response.status_code}")
            debug_print(2,f" >  Raw response content: {response.text}")
    return album_entries

# Parse the json data returned by the Musibrainz api
def parse_response(response, disc_id, folder):
    global global_debug_level
    data = response.json()
    
    tracks = []
    releases = data.get('releases', [])
    for i, release in enumerate(releases):
        for j, media in enumerate(release['media']):
            for k, disc in enumerate(media['discs']):
                if disc['id'] == disc_id:
                    debug_print(2, f" >  release {i}, media {j}, disc {k}, id: {disc.get('id')}")
                    for track in media.get("tracks", []):
                        track_number = track.get("position", 0)
                        track_title = track.get("title", "Unknown Track")
                        artist_names = ", ".join(artist["name"] for artist in track.get("recording", {}).get("artist-credit", []))
                        tracks.append((f"{track_number:02d}", track_title, artist_names))
                        debug_print(3, f"{track_number:02d} {track_title} [{artist_names}]")
                    debug_print(2, f" >  {len(tracks)} tracks found ")
                    return tracks
    return None

# Generate the Bash commands to rename each track
def generate_rename_commands(album_entries):
    global global_debug_level
    rename_commands = []
    for album_entry in album_entries:
        album, tracks = album_entry
        folder, wav_count, disc_id = album
        existing_files = [f for f in os.listdir(folder) if f.lower().endswith(".wav")]
        existing_files.sort()
        
        rename_commands.append(f"\n# === {folder} === ")
        rename_commands.append(f"#   - {len(existing_files)} wav files")
        rename_commands.append(f"#   - {len(tracks)} tracks ")

        for track_number, track_title, artist_names in tracks:
            pattern = re.compile(rf"^{track_number} (.+)\.wav$", re.IGNORECASE)
            for filename in existing_files:
                match = pattern.match(filename)
                if match:
                    new_filename = f"{track_number} {track_title} [{artist_names}].wav"
                    new_filename = re.sub(r'[<>:\"/\\|?*]', '_', new_filename)
                    if filename != new_filename:
                        rename_commands.append(f"mv \"{folder}/{filename}\" \"{folder}/{new_filename}\"")
                    else: 
                        rename_commands.append(f"# skipped: {folder}/{new_filename}")
                    existing_files.remove(filename)
                    break
                else:
                    debug_print(3, f'No match: Tried matching "{filename}" against pattern "{pattern.pattern}"')

    return rename_commands

# Create the shell script that contains all the renaming commands
def create_script(directory, rename_commands, output):
    
    output_file= sanitize_filename("rename_" + output)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    output_file += f"_{timestamp}.sh"

    rename_script = os.path.join(directory, output_file)
    with open(rename_script, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n\n")  
        f.write("\n".join(rename_commands))
    print(f"Script file created: {rename_script}")

# main
def main():
    global global_debug_level
    args = parse_arguments()
    global_debug_level = args.debug if args.debug is not None else 0
    directory = args.path
    folder_like = args.like
    output = args.output

    albums = check_directory(directory, folder_like)    
    album_entries = get_album_data(albums)
    rename_commands = generate_rename_commands(album_entries)
    create_script(directory, rename_commands, output)

if __name__ == "__main__":
    main()
