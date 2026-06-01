# ai-playlist-generator

## Name
AI Playlist Generator

## Description
A Streamlit web app that generates personalised Spotify playlists using AI.
Describe the vibe you're looking for, and the app will find the most relevant tracks and let you save them directly to your Spotify account.

## How it Works
1. You describe what you want, e.g, "chill indie songs for late night coding"
2. An LLM generates 35 candidate tracks via Groq API
3. Track IDs are fetched in parallel from Spotify Web API
4. Track metadata is augmented (URLs, album art, etc)
5. Tracks are semantically ranked using a sentence embedding model, comparing your prompt to each track's description
6. The top 20 tracks are displayed in a card layout
7. Optionally save the playist to your own Spotify acount

## Setup & Installation
Prerequisites:
- Python 3.13.8 (this version of Python was used to build the project)
- Groq API Key (given in the .env file)
- Spotify Web API Client ID and Client Secret (both given in the .env file)

1. Open the repository (cd ai-playlist-generator)
2. Install the necessary Python libraries:
    - Run "pip install -r requirements.txt"
3. Configure environmental variables:
    - If downloading from Moodle, the .env file should already contain the necessary environmental variables
    - If so, you can skip to step 4
    - However, if you're cloning from GitLab, you will need to create your own .env file and add the following:
        - CLIENT_ID="Insert your Spotify Client ID" - will need a Spotify Developer Account for this
        - CLIENT_SECRET="Insert your Spotify Client Secret" - will need a Spotify Developer Account for this
        - GROQ_API_KEY="Insert your Groq API Key" - will need a Groq API Account for this
4. Run the app:
    - Run "streamlit run main.py"

## Usage
1. Enter a prompt in the text box - describe a mood, genre, artist, activity, or anything you like
2. Click "Generate Playlist"
3. Browse the top 20 recommended tracks with album art and Spotify links
4. Click "Save to your Spotify account" to export the playlist (requires Spotify login on first use)

## Tech Stack
- UI: Streamlit
- LLM: Groq API (moonshotai/kimi-k2-instruct-0905)
- Music Data: Spotify Web API (via Spotipy)
- Semantic Ranking: Sentence Transformers (BAAI/bge-small-en-v1.5)
- Structured Output: Pydantic
- Paralellisation: Python ThreadPoolExecutor

## Project Structure
- main.py: orchestrates the pipeline
- groq_client.py: Groq API client and LLM prompt logic
- spotify_client.py: Spotify Web API client, track search, playlist creation
- semantic_ranker.py: Text embedding model and cosine simlarity ranking
- ui.py: Streamlit UI components and progress tracking
- debugging.py: JSON output helper for debugging
- requirements.txt: Python dependencies

## Notes
- The first run will download a sentence-transformer model (roughly 130MB), which may take a moment
- Spotify playlist saving uses OAuth, so you'll be redirected to login and accept permissions on first use
- Debug JSON files are written locally during generation and can be safely deleted
- Should you encounter any issue during generation, a rerun should resolve it
- If the selected LLM (moonshotai/kimi-k2-instruct-0905) becomes deprecated, two other models can be used instead:
    - openai/gpt-oss-120b, llama-3.3-70b-versatile
- If for whatever reason you can not get the app to run, a deployed version can be accessed here:
    - https://ai-playlist-generator.streamlit.app/
    - Note that optional saving playlist feature does not funcion in the deployed version
