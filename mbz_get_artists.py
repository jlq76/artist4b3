import os
import requests
import re
import argparse

# Read arguments
parser = argparse.ArgumentParser(description='Generate a script to rename B3 track files adding artist name based on MusicBrainz data.')
parser.add_argument('directory', help='Directory containing the discid file and .wav files ot the parent directory')
parser.add_argument('--debug', action='store_true', help='Enable debug mode (default: off)')

args = parser.parse_args()
directory = args.directory
debug_mode = args.debug  

# The script expects either:
# - a parent folder with subfolders for each album
# - an album folder that contains the .wav as well as the discid file
if not os.path.exists(directory):
    print(f"Error: Path '{directory}' does not exist.")
    exit(1)


# The script expects a folder (or subfolders) on the brennan that contains the .wav as well as the discid file
# If no discid or no wav files are found in these folders, there is no point to continue.

# Initialize the album  list
albums = []
discards= [] #for debug purpose only

# Check for subfolders
subfolders = [f.path for f in os.scandir(directory) if f.is_dir()]
if subfolders:
    for subfolder in subfolders:
        # print(f"Checking subfolder: {subfolder}")
        wav_files=[]
        discid_path = os.path.join(subfolder, 'discid')
        if os.path.isfile(discid_path):
            with open(discid_path, "r") as file:
                disc_id = file.readline().strip()
            wav_files = [f for f in os.listdir(subfolder) if f.endswith('.wav')]
        if disc_id and wav_files:
            albums.append((subfolder, len(wav_files), disc_id))
        else:
            discards.append(subfolder)
            
else:
    discid_path = os.path.join(directory, 'discid')
    with open(discid_path, "r") as file:
        disc_id = file.readline().strip()
    wav_files = [f for f in os.listdir(directory) if f.endswith('.wav')]
    if disc_id and wav_files:
        albums.append((directory, len(wav_files), disc_id))
    else:
        discards.append(directory)

if debug_mode:
    for album in albums:
        folder, wav_count, disc_id = album
        print(f"Album: {folder}, Number of wav files: {wav_count}, disc_id: {disc_id}")

    for discard in discards:
        print(f"Discarded: {discard}")


album_entries=[]
for album in albums:
    folder, wav_count, disc_id = album
    # Call MusicBrainz API (see https://musicbrainz.org/doc/MusicBrainz_API)
    url = f"https://musicbrainz.org/ws/2/discid/{disc_id}?fmt=json&inc=recordings+artist-credits"
    if debug_mode:
        print(f"Album: {folder}  >>  Calling URL: {url}")
    response = requests.get(url)
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
                        album_entries.append((album, tracks))
                        break

rename_commands = []
for album_entry in album_entries:
    album, tracks = album_entry
    folder, wav_count, disc_id = album
    # Get a list of existing .wav files in the current directory
    existing_files = [f for f in os.listdir(folder) if f.lower().endswith(".wav")]
    
    rename_commands.append(f"\n# === {folder} === ")
    rename_commands.append(f"#   - {len(existing_files)} wav files")
    rename_commands.append(f"#   - {len(tracks)} tracks ")

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
                    rename_commands.append(f"mv \"{folder}/{filename}\" \"{folder}/{new_filename}\"")
                else:
                    rename_commands.append(f"#mv \"{folder}/{filename}\" \"{folder}/{new_filename}\"")
                existing_files.remove(filename)
                # move to next track
                break
            else:
                if debug_mode:
                    print(f'No match: Tried matching "{filename}" against pattern "{pattern.pattern}"')

# create the script file in the target folder

rename_script = os.path.join(directory, "rename_script.sh")
with open(rename_script, "w", encoding="utf-8") as f:
    f.write("#!/bin/bash\n\n")  
    f.write("\n".join(rename_commands))
    print(f"Script file created: {rename_script}")

