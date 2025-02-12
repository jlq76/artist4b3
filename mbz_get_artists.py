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

# Ensure that the discid file exists in the directory
discid_file = os.path.join(directory, "discid")
if not os.path.exists(discid_file):
    print(f"Error: {discid_file} not found in the specified directory.")
    exit(1)

# Read the disc_id from the file
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
    release = data["releases"][0]  # Taking the first release (should be only one per disc_id)
    media = release.get("media", []) # Taking the first media (should be only one per disc_id)

    # Extract track list
    tracks = []
    for k, release in enumerate(data["releases"]):
        media = release.get("media", []) 
        for i, m in enumerate(media):
            discs = m["discs"]
            for j, disc in enumerate(discs):
                found_disc_id= disc.get("id")
                if debug_mode:
                    print(f"release {k}, media {i}, disc {j}, id: {d.get("id")}")
                if found_disc_id == disc_id:
                    print(f"disc_id found in release {k}, media {i}, disc {j}")
                    # Extract track list
                    for track in m.get("tracks", []):
                        track_number = track.get("position", 0)
                        track_title = track.get("title", "Unknown Track")
                        artist_names = ", ".join(artist["name"] for artist in track.get("recording", {}).get("artist-credit", []))
                        tracks.append((f"{track_number:02d}", track_title, artist_names)) 
                    break

    # DEBUG
    if debug_mode:
        print(f"Found {len(tracks)} tracks for this disc_id")

    # Get a list of existing .wav files in the current directory
    existing_files = [f for f in os.listdir(directory) if f.lower().endswith(".wav")]
    if debug_mode:
        print(f"Found {len(existing_files)} WAV files in the directory.")

    if preview_mode:
        rename_commands = []

    # Loop through tracks to find matching files and rename them
    for track_number, track_title, artist_names in tracks:
        if debug_mode:
            print(f"Processing track: {track_number} - {track_title} ({artist_names})")

        # Create a regex pattern to match filenames like "01 Track Title.wav"
        pattern = re.compile(rf"^{track_number} (.+)\.wav$", re.IGNORECASE)

        for filename in existing_files:
            if debug_mode:
                print(f"Checking file: {filename}")
            match = pattern.match(filename)
            if match:
                new_filename = f"{track_number} {match.group(1)} [{artist_names}].wav"
                if filename != new_filename:  # Avoid renaming if already correct
                    if preview_mode: 
                        #rename_commands.append(f"mv \"{os.path.join(directory, filename)}\" \"{os.path.join(directory, new_filename)}\"")
                        rename_commands.append(f"mv \"{filename}\" \"{new_filename}\"")
                    else:
                        if debug_mode:
                            print(f'Renamed: "{filename}" → "{new_filename}"')
                        # os.rename(filename, new_filename)
                    
                    # Ce qui est fait n'est plus à faire...
                    existing_files.remove(filename)
                # move to next track
                break
            else:
                print(f'No match: Tried matching "{filename}" against pattern "{pattern.pattern}"')


    if preview_mode:
        rename_script = os.path.join(directory, "rename_script.sh")
        with open(rename_script, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\n\n")  
            f.write("\n".join(rename_commands))
            
        print(f"Script file created: {rename_script}")

else:
    print(f"Error: Received status code {response.status_code} from MusicBrainz API")
