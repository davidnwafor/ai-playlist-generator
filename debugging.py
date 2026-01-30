import json
# method to save json file
def save(output, filename):
    print(f"[INFO] Writing JSON output to {filename}")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Failed to write JSON output to {filename}")