from sentence_transformers import SentenceTransformer, util
import json
from debugging import save # import debugging json method

# user_input = "give me a trap playlist"
# tracks_list = { 
#     "tracks": [
#         {
#             "artists": "Drake",
#             "track": "Headlines",
#             "description": "A confident, introspective hip-hop anthem where Drake reflects on fame, ambition, and staying true to himself."
#         },
#         {
#             "artists": "Avicii",
#             "track": "Wake Me Up",
#             "description": "An uplifting EDM-folk fusion that captures the restless spirit of youth searching for purpose and belonging."
#         },
#         {
#             "artists": "Taylor Swift",
#             "track": "You Belong With Me",
#             "description": "A catchy country-pop confession of teenage longing and romantic frustration wrapped in relatable storytelling."
#         },
#         {
#             "artists": "Lauryn Hill",
#             "track": "Ex-Factor",
#             "description": "A soulful, emotionally raw R&B ballad about heartbreak, self-worth, and the pain of a toxic relationship."
#         },
#         {
#             "artists": "Kanye West",
#             "track": "Homecoming",
#             "description": "A nostalgic, piano-driven hip-hop track that metaphorically explores Kanye's complex relationship with his hometown and identity."
#         }
#     ]
# }
try:
    # 1. load a pretrained Sentence Transformer model
    print("[INFO] Loading text embedding model...")
    model = SentenceTransformer("all-mpnet-base-v2") # all-MiniLM-L6-v2     all-mpnet-base-v2
except Exception as e:
    print(f"Failed to load embedding model: {e}")
    raise

# method that gets most similar songs
def get_most_similar_tracks(user_input, tracks_list):
    # RETURNS A LIST OF MOST SEMANTIC SIMILAR TRACKS
    print("\n[STEP] RETURNING LIST OF SIMILAR TRACKS")

    try:
        # 2. add context to user input
        user_input = f"Songs that match the vibe of: {user_input}"

        # 3. extract descriptions to a list
        print("[INFO] Extracting track descriptions...")
        if not tracks_list.get("tracks"):
            raise ValueError("No tracks provided for ranking.")

        descriptions = []
        for track in tracks_list["tracks"]:
            descriptions.append(track["description"])
        # print(descriptions)

        # 4. encode user input and descriptions
        print("[INFO] Encoding user input and track descriptions...")
        embeddings = model.encode([user_input] + descriptions, convert_to_tensor=True) # add user_input and descriptions together to make 1 list
        # print(embeddings)

        # 5. compute cosine similarity
        print("[INFO] Computing cosine similarity...")
        similarities = util.cos_sim(embeddings[0], embeddings[1:]) # find the similarity between user input (embeddings[0]) and every description (embeddings[1:])
        # print(similarities)

        # 6. get indices of top tracks
        print("[INFO] Retrieving top indices of top tracks...")
        top_indices = similarities[0].argsort(descending=True) # get the similarities only (similarities[0]) and return the indices that would sort the tensor in desc order (argsort(desc=true))
        # print(top_indices)

        # 7. build ranked list
        print("[INFO] Building ranked list of tracks based on semantic similarity...")
        ranked_tracks = []
        for i in top_indices: # for each index in the top_indices list, which is sorted by similarity
            track = tracks_list["tracks"][i] # get the track at that index
            score = float(similarities[0][i]) # convert the tensor to a float
            track["similarity_score"] = score # store similarity score
            ranked_tracks.append(track) # and add it to the ranked tracks list
        
        n = 20 # number of tracks to return
        print("\n[RESULT] Successfully ranked tracks:")
        print(json.dumps(ranked_tracks[:n], indent=2))
        save(ranked_tracks[:n], "ranked_tracks.json") # save json file for debugging
        return ranked_tracks[:n]
    
    except Exception as e:
        print(f"[ERROR] Unexpected error in get_most_similar_tracks: {e}")

# get_most_similar_tracks(user_input, tracks_list)