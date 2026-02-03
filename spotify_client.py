import spotipy # library for spotify commands
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth # import modules for authentication
import os # for getting exported env variables
from dotenv import load_dotenv # reads variables from .env file and exports them in the os
import json
from debugging import save # import debugging json method

def get_spotify_client():
    # INITIALISES AND RETURNS A SPOTIFY WEB API CLIENT
    print("\n[INFO] Setting up Spotify client...")
    try:
        print("[INFO] Loading environmental varaiables...")
        load_dotenv() # load env variables from .env file

        client_id = os.getenv("CLIENT_ID") # get credentials
        client_secret = os.getenv("CLIENT_SECRET")
        if not client_id:
            print("[ERROR] CLIENT_ID not found in .env file")
            raise EnvironmentError("Missing CLIENT_ID in .env")
        if not client_secret:
            print("[ERROR] CLIENT_SECRET not found in .env file")
            raise EnvironmentError("Missing CLIENT_SECRET in .env")
        
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret) # authenticate and get token
        print("[INFO] Spotify Web client initialised successfully.")

        # token_info = auth_manager.get_access_token() # print contents of token
        # print(token_info)

        return spotipy.Spotify(auth_manager=auth_manager)
    
    except Exception as e:
        print(f"[ERROR] Failed to initialise Spotify client: {e}")
        raise

# method that searches for a track in Spotify and returns its ID
def search_track(artists, song):
    # SEARCHES FOR A SEED TRACK AND RETRIEVES ITS IDS
    print(f"\n[STEP] SEARCHING SPOTIFY FOR TRACK: {song} BY {artists}")

    try:
        sp = get_spotify_client() # start client
        # print(sp.available_markets()) # get country codes, Ireland: IE, UK: GB, America: US

        print(f"[INFO] Searching for: {song} by {artists}...")
        results = sp.search(
            q = f"{artists} {song}",
            limit = 1, # we only need 1 track per search (retrieves the first suggestion)
            type = "track", # we only want tracks from the search, no albums, audiobooks etc
            market = "GB", # different markets have a different pool of selection
        )

        items = results.get("tracks", {}).get("items", []) # retreive the the list of items from the search
        if items:
            print(f"[INFO] Found {len(items)} result(s). Extracting track ID...")
            track_id = items[0].get("id") # get the first ID from the search and return it
            if track_id:
                print(f"\n[RESULT] Track search completed successfully, obtained ID: {track_id}")
                return track_id

        print("[WARN] No results found for this search query.")
        return None # otherwise return null
    
    except spotipy.exceptions.SpotifyException as e:
        print(f"[ERROR] Spotify API error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error in search_tracks: {e}")
        raise

# method that gets track IDs and adds to JSON list of songs
def get_track_ids(tracks):
    # RETRIEVES LIST OF TRACK IDS
    print("\n[STEP] RETRIEVING TRACK IDS")

    try:
        valid_tracks = [] # we'll be adding to this list since we only want track have IDs for
        for t in tracks["tracks"]:
            artists = t["artists"] # get the artists from dictionary
            track = t["track"] # get the track from dictionary
            track_id = search_track(artists, track) # call search method to retrieve ID

            if track_id: # if the ID exists
                print("[INFO] Adding ID to JSON...")
                t["ID"] = track_id
                valid_tracks.append(t)
            else:
                print("[INFO] ID was not found so no ID was added.")

        # we need to guarantee at least 1 ID, so if there's none we will use The Weeknd's Blinding Lights' ID, since it is the biggest song on Spotify
        if not valid_tracks:
            print("[INFO] No IDs were found at all. Using Blinding Lights as backup...")
            valid_tracks.append(
                {
                    "artists": "The Weeknd",
                    "track": "Blinding Lights",
                    "description": "",
                    "ID": "0VjIjW4GlUZAMYd2vXMi3b"
                }
            )
        
        print(f"\n[RESULT] Retrieved IDs for {len(valid_tracks)} out of {len(tracks["tracks"])} tracks:")

        # format returning tracks
        valid_tracks_formatted = {
            "tracks": valid_tracks
        }
        print(json.dumps(valid_tracks_formatted, indent=2))
        save(valid_tracks_formatted, "candidate_tracks_with_ids.json") # save json file for debugging
        return valid_tracks_formatted
    
    except Exception as e:
        print(f"[ERROR] Unexpected error in get_seed_track_ids: {e}")
        raise


# method that gets data of a track from its id
def get_track_data(track_id):
    try:
        sp = get_spotify_client() # start Spotify client
        print("[INFO] Calling Spotify Get Track API...")
        data = sp.track(track_id=track_id, market="GB") # call Spotify Get Track API and save the output
        # extract necessary details from Spotify's output
        track_info = {
            "name": data["name"], # get track name
            "artists": ", ".join([a["name"] for a in data["artists"]]), # get all contribuiting artists
            "spotify_url": data["external_urls"]["spotify"], # get spotify link to play song
            "uri": data["uri"], # get spotify uri for playlist creation
            "album_cover": data["album"]["images"][0]["url"], # 0 = 640 pixels, 1=300 pixels, 2 = 64 pixels
            "album_name": data["album"]["name"], # get album name
        }
        # return json.dumps(track_info, indent=2)
        print(f"[INFO] Retrieved data for {track_info["artists"]} - {track_info["name"]}")
        return track_info
    except spotipy.exceptions.SpotifyException as e:
        print(f"[ERROR] Spotify API error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error in get_track_data: {e}")
        raise

# method that adds details from Spotify to LLM track dictionary 
def update_dataset_of_tracks(tracks_list):
    # RETRIEVES TRACK DATA VIA SPOTIFY
    print("\n[STEP] RETRIEVE NECESSARY TRACK DATA")
    try:
        # loop through track dataset dictionary from LLM
        for t in tracks_list["tracks"]:
            print("[INFO] Updating Track data from Spotify...")
            spotify_track_data = get_track_data(t["ID"]) # call Spotify's Get Track API with an ID and save the output
            t["track"] = spotify_track_data["name"] # update track title in case it's inaccurate
            t["artists"] = spotify_track_data["artists"] # update contributing artists in case it's inaccurate
            t["spotify_url"] = spotify_track_data["spotify_url"] # add the rest of the necessary details
            t["uri"] = spotify_track_data["uri"]
            t["album_cover"] = spotify_track_data["album_cover"]
            t["album_name"] = spotify_track_data["album_name"]
            print("[INFO] Updated Track data")

        print("\n[RESULT] Sucessfully updated track set")
        save(tracks_list, "final_candidate_tracks.json") # save json file for debugging
        return tracks_list
    except Exception as e:
        print(f"[ERROR] Unexpected error in update_dataset_of_tracks: {e}")
        raise

# intialise client with additional settings for user to login to their account
def get_spotify_client_for_user():
    # INITIALISES AND RETURNS A SPOTIFY WEB API CLIENT
    print("\n[INFO] Setting up Spotify user client...")
    try:
        print("[INFO] Loading environmental varaiables...")
        load_dotenv() # load env variables from .env file

        client_id = os.getenv("CLIENT_ID") # get credentials
        client_secret = os.getenv("CLIENT_SECRET")
        if not client_id:
            print("[ERROR] CLIENT_ID not found in .env file")
            raise EnvironmentError("Missing CLIENT_ID in .env")
        if not client_secret:
            print("[ERROR] CLIENT_SECRET not found in .env file")
            raise EnvironmentError("Missing CLIENT_SECRET in .env")
        
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="https://ai-playlist-generator.streamlit.app/callback", # https://ai-playlist-generator.streamlit.app/callback
            scope="playlist-modify-private,playlist-modify-public,"
        ) # authenticate and get token
        print("[INFO] Spotify Web client initialised successfully for user.")

        # token_info = auth_manager.get_access_token() # print contents of token
        # print(token_info)

        return spotipy.Spotify(auth_manager=auth_manager)
    
    except Exception as e:
        print(f"[ERROR] Failed to initialise Spotify client for user: {e}")
        raise

# method for playlist creation
def create_playlist(playlist_name, description):
    # CREATES PLAYLIST FOR USER
    print("\n[STEP] CREATING PLAYLIST FOR USER")
    sp = get_spotify_client_for_user() # start client

    user_id = sp.current_user()["id"] # get user id

    playlist = sp.user_playlist_create( # create playlist
        user = user_id,
        name = playlist_name,
        public = False,
        collaborative = False,
        description = description
    )
    playlist_id = playlist["id"] # get playlist id
    print(f"[INFO] Created playlist: {playlist_id} - {playlist_name}")

    # Adding tracks to the playlist created
    # Opening and reading the JSON file
    with open('ranked_tracks.json', 'r') as f:
        # Parsing the JSON file into a Python dictionary
        data = json.load(f)

    uris = []
    for d in data:
        uris.append(d["uri"])

    sp.playlist_add_items(
        playlist_id = playlist_id,
        items = uris
    )

    print("\n[RESULT] Sucessfully added tracks to playlist")

# create_playlist(playlist_name="Test Playlist by AI", description="User prompt")
