from sentence_transformers import SentenceTransformer, util
import json
from debugging import save # import debugging json method

try:
    # 1. load a pretrained Sentence Transformer model
    print("[INFO] Loading text embedding model...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5") # all-MiniLM-L6-v2     all-mpnet-base-v2
except Exception as e:
    print(f"Failed to load embedding model: {e}")
    raise

# method that gets most similar songs
def get_most_similar_tracks(user_input, tracks_list):
    # RETURNS A LIST OF MOST SEMANTIC SIMILAR TRACKS
    print("\n[STEP] RETURNING LIST OF SIMILAR TRACKS")

    try:
        # 2. add context to user input
        user_input = f"Songs that match the vibe of {user_input}"

        # 3. extract descriptions to a list
        print("[INFO] Extracting track descriptions...")
        if not tracks_list.get("tracks"):
            raise ValueError("No tracks provided for ranking.")

        descriptions = []
        for track in tracks_list["tracks"]:
            check = f"{track["track"]} by {track["artists"]} - {track["description"]}" # format descriptions
            descriptions.append(check)
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
        raise
