import os
import requests
from dotenv import load_dotenv
import sys
import urllib.parse

import re

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")

if not API_KEY or not CSE_ID:
    print("ERROR: Missing API_KEY or CSE_ID in .env file.")
    sys.exit(1)

def clean_snippet(snippet):
    """
    Clean Reddit snippet text to include only user-written content.
    Removes:
      - Dates and times
      - "X points • Y comments • posted by u/username" metadata
      - Avatar mentions
    """
    # Remove typical Reddit post metadata like "123 points • 45 comments • posted by u/username"
    snippet = re.sub(r'\d+\s+points?\s*•\s*\d+\s+comments?\s*•\s*posted by u/\w+', '', snippet, flags=re.IGNORECASE)
    
    # Remove dates like "Jan 1, 2022", "2023-11-18", "18 Nov 2023"
    snippet = re.sub(r'\b(?:\d{1,2}[-/])?\d{1,2}[-/]\d{2,4}\b', '', snippet)
    snippet = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s\d{1,2},?\s\d{4}\b', '', snippet, flags=re.IGNORECASE)
    
    # Remove times like "12:34 PM", "23:45"
    snippet = re.sub(r'\b\d{1,2}:\d{2}(?:\s?[apAP][mM])?\b', '', snippet)
    
    # Remove avatar mentions
    snippet = re.sub(r'\bavatar\b', '', snippet, flags=re.IGNORECASE)
    
    # Remove "posted by u/username" if any remain
    snippet = re.sub(r'posted by u/\w+', '', snippet, flags=re.IGNORECASE)

    # Clean up extra whitespace
    snippet = re.sub(r'\s+', ' ', snippet).strip()
    return snippet

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
        snippet = item.get("snippet", "")
        snippet = clean_snippet(snippet)
        results.append((title, link, snippet))

    return results

def main():
    username = input("Enter Reddit username (without 'u/'): ").strip()
    
    # Create a Google search URL
    google_query = urllib.parse.quote(f'site:reddit.com "u/{username}"')
    google_search_url = f"https://www.google.com/search?q={google_query}"
    
    # Print the link and open in browser
    print(f"\nYou can also browse the results here: {google_search_url}\n")
   

    print(f"Searching Reddit for u/{username} via API...\n")
    results = reddit_user_search(username)

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
