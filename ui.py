import streamlit as st
import json

def setup_display():
    # method that sets up the initial display for the UI

    st.set_page_config(page_title="AI Playlist Generator", layout="wide")
    st.title("David's AI Playlist Generator") # display title
    st.write("Create Spotify playlists in an instant!") # display brief info about app

    with st.form(key="prompt_form"): # create a form to batch user input and submit button together
        # create a text input box where user will input prompt
        prompt = st.text_input(
            "Tell us what you want!",
            placeholder="E.g., chill indie songs for late night coding"
        )
        submitted = st.form_submit_button("Generate Playlist") # create a generate playlist (submit) button
    
    return prompt, submitted # return both the user input and the submission

def display_tracks(session_state_tracks):
    # method that displays tracks after user inputs a prompt

    cols = st.columns(4) # create a list of 4 columns (containers)

    # split the tracks into the columns for easy readability
    for i, track in enumerate(session_state_tracks): # for each index and track in the ranked tracks list
        with cols[i % 4]: # within the current column index; i % 4 gives 0-3, which gives 4 tracks per row
            with st.container(border=True): # within the column border (creates a visual card container with a border)
                # display the necessary track information
                st.image(track["album_cover"],width="stretch") # expands image to fill the container width
                st.write(f"{track['track']}")
                st.caption(track["artists"])
                st.markdown(f"[Listen in Spotify]({track['spotify_url']})")
