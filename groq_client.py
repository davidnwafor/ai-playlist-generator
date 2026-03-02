import os
from groq import Groq
from dotenv import load_dotenv # reads variables from .env file and exports them in the os
import json # for converting response to JSON
from pydantic import BaseModel # for structured JSON response
from debugging import save # import debugging json method

class CandidateTrack(BaseModel): # class for storing track data as a dict
    artists: str
    track: str
    description: str

class CandidateTrackList(BaseModel): # class for storing track dictionaries in a list
    tracks: list[CandidateTrack]

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
        # initial system prompt to set up LLM before user prompt
        system_prompt = """You are a music recommendation expert.

        Your task is to generate a list of real, well-known Spotify tracks that match the user's request.
        ALL tracks must exist on Spotify. Do NOT invent non-existent tracks. Do NOT return albums. Do NOT return duplicate tracks.
        Provide a one-sentence summary for each track, focusing on its mood, lyrical theme and emotional impact.
        Do NOT reference the user's request in the summary, pretend the user's request does not exist when describing the track only.

        Rules:
        - Return a JSON list of EXACTLY 35 tracks.
        - If a track has multiple artists, join them with a comma and a space, e.g, "The Weeknd, JENNIE, Lily-Rose Depp".
        - If the track is credited to a group/duo name on Spotify, use that group/duo name exactly, e.g, use "The Carters" not "Beyoncé, JAY-Z" for "SUMMER"
        - If you are unsure whether a song exists, DO NOT include it.
        - Do NOT return dupllicate tracks.
        - Do NOT reference or include the user's request in the track summaries.
        - Output MUST be valid JSON and match the schema exactly.

        ---

        Example 1:
        User description: "chill late night drive"

        Response:
        {
            "tracks": [
                {
                    "artists": "Drake",
                    "track": "Hold On, We're Going Home",
                    "description": "A silky-smooth '80s-tinged R&B love letter that feels like driving through city lights with the windows down and your heart wide open."
                },
                {
                    "artists": "Frank Ocean",
                    "track": "Nights",
                    "description": "A shape-shifting R&B odyssey that splits your life into before-and-after, capturing the restless energy of late-night overthinking and emotional transition."
                },
                {
                    "artists": "The Weeknd",
                    "track": "After Hours",
                    "description": "A dark, cinematic synth-pop confession where Abel spirals through heartbreak, regret, and desperate attempts to win back love at 3 AM."
                }
            ]
        }

        ---

        Example 2:
        User description: "high energy gym workout music"

        Response:
        {
            "tracks": [
                {
                    "artists": "Travis Scott, Drake",
                    "track": "SICKO MODE",
                    "description": "A shape-shropping Houston fever dream where Travis and Drake trade verses over beat-switch fireworks, capturing the surreal high of living larger than life."
                },
                {
                    "artists": "Logic",
                    "track": "Keanu Reeves",
                    "description": "A swagger-heavy flex track that pairs rapid-fire punchlines with cinematic strings, letting Logic brag about action-hero fame while winking at the audience."
                },
                {
                    "artists": "Future",
                    "track": "Stick Talk",
                    "description": "A menacing trap banger dripping with lean-soaked confidence, where Future turns street paranoia into a hypnotic celebration of power and survival."
                }
            ]
        }

        ---

        Example 3:
        User description: "sad rnb breakup songs"

        Response:
        {
            "tracks": [
                {
                    "artists": "SZA",
                    "track": "Nobody Gets Me",
                    "description": "A heartbreakingly raw alt-R&B ballad where SZA's cracked vocals plead over lonely guitar, begging one last lover to stay because no one else sees her clearly."
                },
                {
                    "artists": "Summer Walker",
                    "track": "Playing Games",
                    "description": "A smoky, slow-burn R&B warning shot that mixes playful melodies with cold honesty, calling out a partner who texts sweet nothings while hiding the truth."
                },
                {
                    "artists": "Lauryn Hill",
                    "track": "Ex-Factor",
                    "description": "A timeless, aching neo-soul confession where Lauryn's velvet voice untangles love's contradictions, turning personal pain into a universal hymn for anyone stuck on repeat."
                }
            ]
        }

        ---

        Example 4:
        User description: "Kanye West songs"

        Response:
        {
            "tracks": [
                {
                    "artists": "Kanye West, Chris Martin",
                    "track": "Homecoming",
                    "description": "A bittersweet piano-laced love letter to Chicago, where Kanye personifies his hometown as a childhood sweetheart and wrestles with the guilt of leaving her for fame."
                },
                {
                    "artists": "Kanye West",
                    "track": "Diamonds From Sierra Leone",
                    "description": "A lavish soul-sample banger that sparkles with bravado before twisting into a guilt-ridden meditation on blood diamonds and the true cost of hip-hop luxury."
                },
                {
                    "artists": "Kanye West, Big Sean, 2 Chainz, Pusha T",
                    "track": "Mercy",
                    "description": "A trunk-rattling posse cut built on eerie synths and slow-rolling swagger, where four MCs trade flamboyant punchlines about cars, women, and success over a hauntingly sparse beat."
                }
            ]
        }
        """

        print("[DEBUG] Sending tracks request to Groq API...")
        response = client.chat.completions.create(
            model="moonshotai/kimi-k2-instruct-0905", # openai/gpt-oss-120b llama-3.3-70b-versatile
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
            },
            temperature=0.6 # controls randomness
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
