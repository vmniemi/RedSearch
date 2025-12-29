import requests
import urllib.parse
import time
import os
import csv
import json
from datetime import datetime, timezone


#  Helper Functions 

def fetch_json(url, retries=3):
    headers = {"User-Agent": "RedSearchScript by u/yourusername"}
    for _ in range(retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            time.sleep(2)
        else:
            print(f"Error fetching {url}: {response.status_code}")
            return None
    return None


def fetch_user_comments(username, limit, paginate=False):
    comments = []
    after = None
    remaining = limit

    while remaining > 0:
        batch_size = min(100, remaining)
        url = f"https://www.reddit.com/user/{username}/comments.json?limit={batch_size}"
        if after:
            url += f"&after={after}"

        data = fetch_json(url)
        if not data or not data["data"]["children"]:
            break

        for c in data["data"]["children"]:
            comments.append(c["data"])

        remaining -= len(data["data"]["children"])
        after = data["data"].get("after")

        if not paginate or not after:
            break

    return comments


def fetch_user_posts(username, limit, paginate=False):
    posts = []
    after = None
    remaining = limit

    while remaining > 0:
        batch_size = min(100, remaining)
        url = f"https://www.reddit.com/user/{username}/submitted.json?limit={batch_size}"
        if after:
            url += f"&after={after}"

        data = fetch_json(url)
        if not data or not data["data"]["children"]:
            break

        for p in data["data"]["children"]:
            posts.append(p["data"])

        remaining -= len(data["data"]["children"])
        after = data["data"].get("after")

        if not paginate or not after:
            break

    return posts


def normalize_item(item, item_type, username):
    created_utc = item.get("created_utc", 0)
    text = item.get("body") or item.get("selftext") or ""

    return {
        "username": username,
        "type": item_type,
        "subreddit": item.get("subreddit", ""),
        "text": text,
        "permalink": "https://www.reddit.com" + item.get("permalink", ""),
        "score": item.get("score", 0),
        "created_utc": created_utc,
        "created_datetime": datetime.fromtimestamp(created_utc, timezone.utc).isoformat(),
        "source": "reddit_json",
        "retrieved_at": datetime.now(timezone.utc).isoformat()
    }

def save_to_csv(results, username):
    os.makedirs("data/csv", exist_ok=True)
    filename = f"data/csv/{username}_{datetime.now(timezone.utc).isoformat()}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"[+] CSV saved: {filename}")


def save_to_json(results, username):
    os.makedirs("data/json", exist_ok=True)
    filename = f"data/json/{username}_{datetime.now(timezone.utc).isoformat()}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"[+] JSON saved: {filename}")


#  Main Program 

def main():
    print("Select mode:")
    print("1 - Light (10 comments, optional posts)")
    print("2 - Medium (30 comments + 30 posts)")
    print("3 - Max (all available comments and posts)")
    mode = input("Enter mode (1/2/3): ").strip()

    if mode == "1":
        comment_limit = 10
        post_limit = 10
        light_mode = True
        paginate = False
    elif mode == "2":
        comment_limit = 30
        post_limit = 30
        light_mode = False
        paginate = False
    elif mode == "3":
        comment_limit = 10000
        post_limit = 10000
        light_mode = False
        paginate = True
    else:
        print("Invalid mode.")
        return

    username = input("Enter Reddit username (without 'u/'): ").strip()

    # Google search link
    google_query = urllib.parse.quote(f'site:reddit.com "u/{username}"')
    print(f"\nGoogle search link:\nhttps://www.google.com/search?q={google_query}\n")

    comments = fetch_user_comments(username, comment_limit, paginate)
    posts = []

    print(f"\nComments by u/{username}:\n")
    for c in comments:
        print(f"u/{username} in r/{c['subreddit']}: {c.get('body','')}")
        print(f"Link: https://www.reddit.com{c['permalink']}")
        print("-" * 60)

    show_posts = True
    if light_mode:
        show_posts = input("\nShow posts? (y/n): ").lower() == "y"

    if show_posts:
        posts = fetch_user_posts(username, post_limit, paginate)
        print(f"\nPosts by u/{username}:\n")
        for p in posts:
            text = p.get("title", "")
            if p.get("selftext"):
                text += "\n" + p["selftext"]
            print(f"u/{username} in r/{p['subreddit']}: {text}")
            print(f"Link: https://www.reddit.com{p['permalink']}")
            print("-" * 60)

    # Save structured results
    all_results = []
    for c in comments:
        all_results.append(normalize_item(c, "comment", username))
    for p in posts:
        all_results.append(normalize_item(p, "post", username))

    if all_results:
        save_to_csv(all_results, username)
        save_to_json(all_results, username)
    else:
        print("No data to save.")


if __name__ == "__main__":
    main()
