import json
import subprocess
import os

# Load JSON file
with open('apollo_info.json', 'r') as f:
    data = json.load(f)

# Extract all URLs
urls = []
modules = data["data"]["classBySlug"]["modules"]["nodes"]

for module in modules:
    for session in module["sessions"]["nodes"]:
        media_nodes = session["media"]["nodes"]
        if len(media_nodes) > 3 and "url" in media_nodes[3]:
            urls.append(media_nodes[3]["url"])

# Download each URL and name it N2A_XX.mp3
for index, url in enumerate(urls, start=1):
    filename = f"Jacob_{index:02d}.mp3"
    print(f"\n⬇️ Downloading {filename} from {url}")
    try:
        subprocess.run([
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "-o", filename,
            url
        ], check=True)
        print(f"✅ Saved as {filename}")
    except subprocess.CalledProcessError:
        print(f"❌ Failed to download {url}")
