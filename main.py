from groq_client import *
from spotify_client import *
import json
from semantic_ranker import *
from ui import *
import streamlit as st

# 1. set up ui
prompt, submitted = setup_display() # get user prompt and submission

# initialise session state
if "generated" not in st.session_state:
    st.session_state.generated = False
if "ranked_tracks" not in st.session_state:
    st.session_state.ranked_tracks = []

# run main logic only when user submits a prompt
if submitted and prompt.strip():
    with st.spinner("Generating playlist..."):

        # 2. get user input
        user_input = prompt

        # 3. extract a dataset of tracks from an llm
        dataset_of_tracks = prompt_llm_for_dataset(user_input) # store as dictionary

        # 4. extract a description of each track from an llm
        dataset_of_tracks_with_descriptions = prompt_llm_for_descriptions(json.dumps(dataset_of_tracks, indent=2)) # send tracks dict as a JSON string first - store as dictionary

        # 5. retrieve ids for each track via spotify
        dataset_of_tracks_with_ids_and_desc = get_track_ids(dataset_of_tracks_with_descriptions) # store as dictionary

        # 6. get more data via spotify
        updated_tracks = update_dataset_of_tracks(dataset_of_tracks_with_ids_and_desc)

        # 7. find most similar tracks using an embedding model
        top_tracks = get_most_similar_tracks(user_input, updated_tracks) # store as list

        # update session state
        st.session_state.ranked_tracks = top_tracks
        st.session_state.generated = True

# display tracks if available
if st.session_state.generated:
    # 8. optional step for user to save playlist to their account
    if st.button("Save to your Spotify account"):
        with st.spinner("Saving playlist..."):
            create_playlist(playlist_name="AI Playlist", description=prompt)
        st.success("Playlist saved!")

    display_tracks(st.session_state.ranked_tracks)