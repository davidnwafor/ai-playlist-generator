import spotipy # library for spotify commands
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth # import modules for authentication
import os # for getting exported env variables
from dotenv import load_dotenv # reads variables from .env file and exports them in the os
import json
from debugging import save # import debugging json method
import webbrowser # for opening playlist in a new tab
from concurrent.futures import ThreadPoolExecutor, as_completed # for parellisation

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
def search_track(sp, artists, song):
    # SEARCHES FOR A SEED TRACK AND RETRIEVES ITS IDS
    print(f"\n[STEP] SEARCHING SPOTIFY FOR TRACK: {song} BY {artists}")

    try:
        # sp = get_spotify_client() # start client
        # print(sp.available_markets()) # get country codes, Ireland: IE, UK: GB, America: US

        print(f"[INFO] Searching for: {song} by {artists}...")
        results = sp.search(
            q = f"{artists} {song}",
            limit = 1, # we only need 1 track per search (retrieves the first suggestion)
            type = "track", # we only want tracks from the search, no albums, audiobooks etc
            market = "US", # different markets have a different pool of selection
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

# method that gets all data of tracks from a list of ids
def get_tracks_data(sp, track_ids):
    try:
        # sp = get_spotify_client() # start Spotify client
        print("[INFO] Calling Spotify Get Track API...")
        # data = sp.tracks(tracks=track_ids, market="GB") # call Spotify Get Track API and save the output NOTE: no longer needed because of migration 9/3/25
        # return data
        # NOTE: the below logic replicates the deprecated batch Several Tracks call (9/3/25) using threads
        # RETRIEVES TRACK DATA IN PARALLEL
        if not track_ids: # safety check for if no ids were passed in
            print("[WARN] No track IDs provided.")
            return {"tracks": []}
        
        def _get_one(index, track_id): # helper function that gets data 1 Spotify track
            tr = sp.track(track_id, market="US") # call Spotify Get Track
            return index, tr # returning index to store original placement
        
        tracks = [None] * len(track_ids) # placeholder list to be filled

        with ThreadPoolExecutor(max_workers=10) as ex: # create a pool of 10 worker threads
            futures = [ # submit all API calls to run concurrently
                ex.submit(_get_one, i, track_id)
                for i, track_id in enumerate(track_ids)
            ]
            
            for f in as_completed(futures): # loop over results as each thread finishes
                index, tr = f.result() # get index and track response from thread result
                tracks[index] = tr # store track response in correct position
                print(f"[INFO] Retrieved data for track {index}!")

        print("\n[RESULT] Successfully retrieved tracks metadata\n")
        return {"tracks": tracks} # return results in the same structure as old Spotify Get Several Tracks response

    except spotipy.exceptions.SpotifyException as e:
        print(f"[ERROR] Spotify API error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error in get_track_data: {e}")
        raise

# method that adds details from Spotify to LLM track dictionary 
def update_dataset_of_tracks(sp, tracks_list):
    # RETRIEVES TRACK DATA VIA SPOTIFY
    print("\n[STEP] RETRIEVE NECESSARY TRACK DATA")
    try:
        ids = [] # extract ids into a list
        for t in tracks_list["tracks"]:
            ids.append(t["ID"])

        if not ids:
            print("[WARN] No track IDs found.")
            return tracks_list

        tracks_resp = get_tracks_data(sp, ids) # call Spotify's Get Several Tracks API with list of all IDs and save output

        for t, tr in zip(tracks_list["tracks"], tracks_resp["tracks"]): # loop through both tracks and API response lists
            if not tr: # if for some reason the API track response doesn't exist, skip
                print(f"[WARN] Spotify returned None for ID={t.get('ID')}")
                continue

            print("[INFO] Updating Track data from Spotify...")
            t["track"] = tr["name"] # get track name and update in case it's inaccurate
            t["artists"] = ", ".join([a["name"] for a in tr["artists"]]) # get all contribuiting artists and update in case it's inaccurate
            t["spotify_url"] = tr["external_urls"]["spotify"] # get spotify link to play song
            t["uri"] = tr["uri"] # get spotify uri for playlist creation
            t["album_cover"] = tr["album"]["images"][0]["url"] # 0 = 640 pixels, 1=300 pixels, 2 = 64 pixels
            t["album_name"] = tr["album"]["name"] # get album name
            print(f"[INFO] Updated {t['artists']} - {t['track']}")

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

    # user_id = sp.current_user()["id"] # get user id # NOTE: no longer needed because of migration 9/3/25

    playlist = sp.current_user_playlist_create( # create playlist
        # user = user_id, # NOTE: no longer needed because of migration 9/3/25
        name = playlist_name,
        public = False,
        collaborative = False,
        description = description
    )
    playlist_id = playlist["id"] # get playlist id
    playlist_url = playlist["external_urls"]["spotify"] # get playlist url
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

    webbrowser.open_new_tab(playlist_url) # open playlist in a new tab

# method that gets track IDs concurrently and adds to JSON list of songs
def get_track_ids_parallel(sp, tracks):
    # Parallel version of get_track_ids()
    # RETRIEVES LIST OF TRACK IDS
    print("\n[STEP] RETRIEVING TRACK IDS")

    try:
        valid_tracks = [] # we'll be adding to this list since we only want track have IDs for

        def _search_one(t): # helper function that searches for 1 Spotify track
            artists = t["artists"] # get the artists from dictionary
            track = t["track"] # get the track from dictionary
            track_id = search_track(sp, artists, track) # call search method to retrieve ID
            return t, track_id # return both the original track dictionary and retrieved ID, that way we can attach the ID later

        # create a pool of worker threads, max_workers is how many run at once - in this case, 10
        with ThreadPoolExecutor(max_workers=10) as ex:
            # submit all track searches to run in parallel
            futures = [] # initial list of Future objects
            for t in tracks["tracks"]:
                future = ex.submit(_search_one, t) # start the function in a new thread, which returns a Future object
                futures.append(future) # collect returned Future object and store in a list

            # iterate over results as soon as each thread finishes
            for f in as_completed(futures):
                # as_completed(...) yields futures in the order they finish, not the order they started
                t, track_id = f.result() # unpack the tupled result
                if track_id: # if the id exists
                    print("[INFO] Adding ID to JSON...")
                    t["ID"] = track_id
                    valid_tracks.append(t)
                else:
                    print("[INFO] ID was not found so no ID was added.")

        # we need to guarantee at least 1 ID, so if there's none we will use The Weeknd's Blinding Lights' ID, since it is the biggest song on Spotify
        if not valid_tracks:
            print("[INFO] No IDs were found at all. Using Blinding Lights as backup...")
            valid_tracks.append({
                "artists": "The Weeknd",
                "track": "Blinding Lights",
                "description": "",
                "ID": "0VjIjW4GlUZAMYd2vXMi3b"
            })

        print(f"\n[RESULT] Retrieved IDs for {len(valid_tracks)} out of {len(tracks["tracks"])} tracks:")
        # format returning tracks
        valid_tracks_formatted = {
            "tracks": valid_tracks
        }
        print(json.dumps(valid_tracks_formatted,indent=2))
        save(valid_tracks_formatted, "candidate_tracks_with_ids.json") # save json file for debugging
        return valid_tracks_formatted
    except Exception as e:
        print(f"[ERROR] Unexpected error in get_track_ids_parallel: {e}")
        raise
