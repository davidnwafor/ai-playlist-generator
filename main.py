from groq_client import *
from spotify_client import *
from semantic_ranker import *
from ui import *
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
import time

# function that runs the playlist generation using the user input
def generate_playlist(user_input):
    # 1. set up clients
    gr = get_groq_client() # start groq client
    sp = get_spotify_client() # start spotify client

    # 2. extract a dataset of tracks from an llm
    dataset_of_tracks = prompt_llm_for_dataset(gr, user_input) # store as dictionary

    # 3. retrieve ids for each track via spotify
    dataset_of_tracks_with_ids = get_track_ids_parallel(sp, dataset_of_tracks) # store as dictionary

    # 4. get more data via spotify
    updated_tracks = update_dataset_of_tracks(sp, dataset_of_tracks_with_ids)

    # 5. find most similar tracks using an embedding model
    top_tracks = get_most_similar_tracks(user_input, updated_tracks) # store as list

    return top_tracks

# 1. set up ui
prompt, submitted = setup_display() # get user prompt and submission
initialise_session_state() # initialised session state variables

# 2. run main logic only when user submits a prompt
if submitted and prompt.strip():
    ui = ProgressUI() # create a UI Progress class
    user_input = prompt.strip() # get user input
    
    # run generation in background, using another thread, so UI can keep updating
    with ThreadPoolExecutor(max_workers=1) as ex: # using a thread pool of 1 thread allows playlist generation to run without streamlit ui freezing
        fut = ex.submit(generate_playlist, user_input) # start running playlist generation in the background, using a Future object

        # animate progress while generating (targeting around 10 secs, capped at 95% until done)
        while not fut.done(): # keep looping as long as playlist generation is not complete
            ui.update() # update ui
            time.sleep(0.1) # pause briefly for 100ms so we don't overload cpu

        # when done
        top_tracks = fut.result() # get top tracks from background thread
        ui.done() # run ui completion update

        # update session state variables
        st.session_state.ranked_tracks = top_tracks
        st.session_state.generated = True

# 3. display tracks if available
if st.session_state.generated:
    # 8. optional step for user to save playlist to their account
    if st.button("Save to your Spotify account"):
        with st.spinner("Saving playlist..."):
            create_playlist(playlist_name="AI Playlist", description=prompt)
        st.success("Playlist saved!")

    display_tracks(st.session_state.ranked_tracks)
