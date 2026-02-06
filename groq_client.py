import os
from groq import Groq
from dotenv import load_dotenv # reads variables from .env file and exports them in the os
import json # for converting response to JSON
from pydantic import BaseModel # for structured JSON response
from debugging import save # import debugging json method

class CandidateTrack(BaseModel): # class for storing track data as a dict
    artists: str
    track: str

class CandidateTrackList(BaseModel): # class for storing track dictionaries in a list
    tracks: list[CandidateTrack]

class DescribedTrack(BaseModel): # class for storing track data with description as a dict
    artists: str
    track: str
    description: str

class DescribedTrackList(BaseModel): # class for storing updated track dictionaries in a list
    tracks: list[DescribedTrack]

# Global setup
# user_prompt = "hype trap songs" # user prompt

def get_groq_client(): # method that returns Groq API client
    # INITIALISES AND RETURNS A GROQ API CLIENT
    print("\n[INFO] Setting up Groq client...")
    try:
        print("[INFO] Loading environmental varaiables...")
        load_dotenv() # load env variable from .env file

        api_key = os.getenv("GROQ_API_KEY") # get credential
        if not api_key:
            print("[ERROR] GROQ_API_KEY not found in .env file")
            raise EnvironmentError("Missing GROQ_API_KEY in .env")

        client = Groq(api_key=api_key,)
        print("[INFO] Groq client initialised successfully.")
        return client
    
    except Exception as e:
        print(f"[ERROR] Failed to initialise Groq client: {e}")
        raise

# LLM for track dataset extraction
def prompt_llm_for_dataset(client, user_input):
    # SENDS A USER DESCRIPTION TO GROQ AND RETRIEVES 50 TRACKS
    print("\n[STEP] Extracting dataset of tracks from user prompt...")
    try:
        # client = get_groq_client() # get Groq API client

        # initial system prompt to set up LLM before user prompt
        system_prompt = """You are a music recommendation expert.
        Given a user description, return 50 real, well-known Spotify songs that either fit the mood or suit the user's request.
        Only return a JSON list of song titles and artists. Do not invent non-existent songs.
        If a track has multiple artists, join them with a comma and a space, e.g, "The Weeknd, JENNIE, Lily-Rose Depp"

        Respond only with JSON using this format:
        {
            "tracks": [
                {
                    "artists": "Drake",
                    "track": "Headlines"
                },
                {
                    "artists": "Avicii",
                    "track": "Wake Me Up"
                },
                {
                    "artists": "Taylor Swift",
                    "track": "You Belong With Me"
                },
                {
                    "artists": "Lauryn Hill",
                    "track": "Ex-Factor"
                },
                {
                    "artists": "Kanye West, Chris Martin",
                    "track": "Homecoming"
                }
            ]
        }
        """

        print("[DEBUG] Sending tracks request to Groq API...")
        response = client.chat.completions.create(
                model="openai/gpt-oss-120b", # openai/gpt-oss-120b llama-3.3-70b-versatile
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": user_input
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "candidate_tracks",
                        "schema": CandidateTrackList.model_json_schema()
                    }
                }
            )

        print("[DEBUG] Raw LLM response received. Attempting to parse JSON output...")
        tracks = json.loads(response.choices[0].message.content)

        print("\n[RESULT] Dataset of tracks extracted successfully:")
        tracks_json = json.dumps(tracks, indent=2)
        print(tracks_json)

        save(tracks, "initial_candidate_tracks.json") # save json file for debugging
        return tracks
    
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON response: {e}")
        print("[DEBUG] Raw output was:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"[ERROR] Unexpected error in prompt_llm_for_dataset: {e}")

# LLM for track descriptions
def prompt_llm_for_descriptions(client, list_of_tracks):
    # SENDS TRACKS TO GROQ TO RETRIEVE DESCRIPTIONS
    print("\n[STEP] Generating descriptions for each track...")
    try:
        # client = get_groq_client() # get Groq API client

        # initial system prompt to set up LLM before user prompt
        system_prompt = """You are a music recommendation expert.
        Given a JSON list of songs, containing artists and track information, write a one-sentence summary for each song. Focus on its mood, lyrical theme, genre and emotional impact. Avoid technical jargon and make it sound like a music critic describing the song to friend.
        Return the given JSON list of song titles and artists with a description added to each entry.

        Respond only with JSON using this format:
        {
            "tracks": [
                {
                    "artists": "Drake",
                    "track": "Headlines",
                    "description": "A confident, introspective hip-hop anthem where Drake reflects on fame, ambition, and staying true to himself."
                },
                {
                    "artists": "Avicii",
                    "track": "Wake Me Up",
                    "description": "An uplifting EDM-folk fusion that captures the restless spirit of youth searching for purpose and belonging."
                },
                {
                    "artists": "Taylor Swift",
                    "track": "You Belong With Me",
                    "description": "A catchy country-pop confession of teenage longing and romantic frustration wrapped in relatable storytelling."
                },
                {
                    "artists": "Lauryn Hill",
                    "track": "Ex-Factor",
                    "description": "A soulful, emotionally raw R&B ballad about heartbreak, self-worth, and the pain of a toxic relationship."
                },
                {
                    "artists": "Kanye West, Chris Martin",
                    "track": "Homecoming",
                    "description": "A nostalgic, piano-driven hip-hop track that metaphorically explores Kanye's complex relationship with his hometown and identity."
                }
            ]
        }
        """

        print("[DEBUG] Sending descriptions request to Groq API...")
        response = client.chat.completions.create(
                model="openai/gpt-oss-120b", # openai/gpt-oss-120b llama-3.3-70b-versatile
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": list_of_tracks
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "described_tracks",
                        "schema": DescribedTrackList.model_json_schema()
                    }
                }
            )

        print("[DEBUG] Raw LLM response received. Attempting to parse JSON output...")
        tracks = json.loads(response.choices[0].message.content)

        print("\n[RESULT] Descriptions of tracks extracted successfully:")
        tracks_json = json.dumps(tracks, indent=2)
        print(tracks_json)

        save(tracks, "described_candidate_tracks.json") # save json file for debugging
        return tracks
    
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON response: {e}")
        print("[DEBUG] Raw output was:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"[ERROR] Unexpected error in prompt_llm_for_descriptions: {e}")


# prompt_llm_for_descriptions(json.dumps(prompt_llm_for_dataset(user_prompt), indent=2))
