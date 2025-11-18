import os
import requests
from dotenv import load_dotenv
import sys

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")

if not API_KEY or not CSE_ID:
    print("ERROR: Missing API_KEY or CSE_ID in .env file.")
    sys.exit(1)

def reddit_user_search(username):
    query = f'site:reddit.com "u/{username}"'
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CSE_ID,
        "q": query,
        "num": 10
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("Error:", response.text)
        return []

    data = response.json()
    results = []

    if "items" not in data:
        print("No results found.")
        return results

    for item in data["items"]:
        title = item.get("title")
        link = item.get("link")
        snippet = item.get("snippet")
        results.append((title, link, snippet))

    return results

def main():
    username = input("Enter Reddit username (without 'u/'): ").strip()
    print(f"\nSearching Reddit for u/{username}...\n")

    results = google_reddit_user_search(username)

    if not results:
        print("No results.")
        return

    for i, (title, link, snippet) in enumerate(results, start=1):
        print(f"Result #{i}")
        print("Title:", title)
        print("Link:", link)
        print("Snippet:", snippet)
        print("-" * 60)

if __name__ == "__main__":
    main()
