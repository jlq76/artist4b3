import os
import requests
import re
import argparse

# Read arguments
parser = argparse.ArgumentParser(description='Rename B3 track files to add artist name based on MusicBrainz data.')
parser.add_argument('directory', help='Directory containing the discid file and .wav files')
parser.add_argument('--debug', action='store_true', help='Enable debug mode (default: off)')
parser.add_argument('--preview', action='store_true', help='Generate a bash script to preview renaming actions (default: off)')

args = parser.parse_args()
directory = args.directory
debug_mode = args.debug  
preview_mode = args.preview 

# The script expects a folder on the brennan that contains the .wav as well as the discid file
# If no discid is found, there is no point to continue.
# Ensure that the discid file exists in the directory in parameter
discid_file = os.path.join(directory, "discid")
if not os.path.exists(discid_file):
    print(f"Error: {discid_file} not found in the specified directory.")
    exit(1)

# Read the disc_id from the file (only the first line is needed)
with open(discid_file, "r") as file:
    disc_id = file.readline().strip()

# Call MusicBrainz API (see https://musicbrainz.org/doc/MusicBrainz_API)
url = f"https://musicbrainz.org/ws/2/discid/{disc_id}?fmt=json&inc=recordings+artist-credits"
if debug_mode:
    print(f"Calling URL: {url}")
response = requests.get(url)

# Parse the received json data 
if response.status_code == 200:
    data = response.json()

    # browse through the releases, media and discs until the correct disc_id is found
    tracks = []
    releases = data.get('releases', [])
    for i, release in enumerate(releases):
        for j, media in enumerate(release['media']):
            for k, disc in enumerate(media['discs']):
                if disc['id'] == disc_id:
                    if debug_mode:
                        print(f"release {i}, media {j}, disc {k}, id: {disc.get("id")}")
                    for track in media.get("tracks", []):
                        track_number = track.get("position", 0)
                        track_title = track.get("title", "Unknown Track")
                        artist_names = ", ".join(artist["name"] for artist in track.get("recording", {}).get("artist-credit", []))
                        tracks.append((f"{track_number:02d}", track_title, artist_names)) 
                    break
    # if no tracks found, then exit
    if not tracks:
        print(f"no tracks found for disc_id {disc_id}; exiting now...")
        exit(1)

    if debug_mode:
        print(f"Found {len(tracks)} tracks for this disc_id")

    # Get a list of existing .wav files in the current directory
    existing_files = [f for f in os.listdir(directory) if f.lower().endswith(".wav")]
    if debug_mode:
        print(f"Found {len(existing_files)} WAV files in the directory.")

    if len(existing_files) != len(tracks):
        print(f"{'-' * 70}\n !! The number of files ({len(existing_files)}) and number of tracks ({len(tracks)}) don't match !!\n{'-' * 70}")

    if preview_mode:
        rename_commands = []

    # Loop through tracks to find matching files and rename them
    for track_number, track_title, artist_names in tracks:
        # Create a regex pattern to match filenames like "01 Track Title.wav"
        pattern = re.compile(rf"^{track_number} (.+)\.wav$", re.IGNORECASE)
        for filename in existing_files:
            match = pattern.match(filename)
            if match:
                # new_filename = f"{track_number} {match.group(1)} [{artist_names}].wav"
                new_filename = f"{track_number} {track_title} [{artist_names}].wav"
                # new_filename = re.sub(r'[^A-Za-z0-9_\- .\[\]]', '_', new_filename)
                new_filename = re.sub(r'[<>:"/\\|?*]', '_', new_filename)

                if filename != new_filename:  # Avoid renaming if already correct
                    if preview_mode: 
                        rename_commands.append(f"mv \"{filename}\" \"{new_filename}\"")
                    else:
                        # os.rename(filename, new_filename)
                        print(f'Renamed: "{filename}" → "{new_filename}"')
                    # Ce qui est fait n'est plus à faire...
                    existing_files.remove(filename)
                # move to next track
                break
            else:
                if debug_mode:
                    print(f'No match: Tried matching "{filename}" against pattern "{pattern.pattern}"')

    # create the script file in the target folder
    if preview_mode:
        rename_script = os.path.join(directory, "rename_script.sh")
        with open(rename_script, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\n\n")  
            f.write("\n".join(rename_commands))
            print(f"Script file created: {rename_script}")
else:
    print(f"Error: Received status code {response.status_code} from MusicBrainz API")
