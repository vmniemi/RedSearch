import requests
import urllib.parse
import time
import os


def fetch_json(url, retries=3):
    headers = {"User-Agent": "RedSearchScript by u/yourusernamehere"}
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
        if not data or 'data' not in data or not data['data']['children']:
            break
        for c in data['data']['children']:
            comments.append(c['data']['body'])
        remaining -= len(data['data']['children'])
        after = data['data'].get('after')
        if not after or not paginate:
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
        if not data or 'data' not in data or not data['data']['children']:
            break
        for p in data['data']['children']:
            title = p['data'].get('title', '')
            selftext = p['data'].get('selftext', '')
            full_text = title
            if selftext and selftext not in ['[removed]', '[deleted]']:
                full_text += "\n" + selftext
            posts.append(full_text)
        remaining -= len(data['data']['children'])
        after = data['data'].get('after')
        if not after or not paginate:
            break
    return posts

def save_results(username, comments, posts):
    filename = f"{username}_results.txt"
    with open(filename, "w", encoding="utf-8") as f:
        if comments:
            f.write(f"Comments by u/{username}:\n\n")
            for c in comments:
                f.write(f"u/{username}: {c}\n{'-'*60}\n")
        if posts:
            f.write(f"\nPosts by u/{username}:\n\n")
            for p in posts:
                f.write(f"u/{username}: {p}\n{'-'*60}\n")
    print(f"\nResults saved to {os.path.abspath(filename)}")


def main():
    print("Select mode:")
    print("1 - Light (10 comments, optional posts)")
    print("2 - Medium (30 comments + 30 posts)")
    print("3 - Max (all available comments and posts)")
    mode = input("Enter mode (1/2/3): ").strip()

    if mode == '1':
        comment_limit = 10
        post_limit = 10
        light_mode = True
        paginate = False
    elif mode == '2':
        comment_limit = 30
        post_limit = 30
        light_mode = False
        paginate = False
    elif mode == '3':
        comment_limit = 10000  
        post_limit = 10000
        light_mode = False
        paginate = True
    else:
        print("Invalid mode. Exiting.")
        return

    username = input("Enter Reddit username (without 'u/'): ").strip()

    
    google_query = urllib.parse.quote(f'site:reddit.com "u/{username}"')
    google_search_url = f"https://www.google.com/search?q={google_query}"
    print(f"\nYou can also browse the results here: {google_search_url}\n")
    

    
    comments = fetch_user_comments(username, comment_limit, paginate)
    if comments:
        print(f"Comments by u/{username}:\n")
        for c in comments:
            print(f"u/{username}: {c}\n{'-'*60}")
    else:
        print(f"No comments found for u/{username}.")

    show_posts = True
    if light_mode:
        choice = input("\nDo you want to see posts? (y/n): ").strip().lower()
        show_posts = (choice == 'y')

    posts = []
    if show_posts:
        posts = fetch_user_posts(username, post_limit, paginate)
        if posts:
            print(f"\nPosts by u/{username}:\n")
            for p in posts:
                print(f"u/{username}: {p}\n{'-'*60}")
        else:
            print(f"No posts found for u/{username}.")

    
    save_choice = input("\nDo you want to save the results to a file? (y/n): ").strip().lower()
    if save_choice == 'y':
        save_results(username, comments, posts)

if __name__ == "__main__":
    main()
