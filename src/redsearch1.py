import requests
import urllib.parse
import time
import os
import csv
import json
import re
from datetime import datetime, timezone

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer

# Detoxify is optional because it can be slow/heavy.
USE_TOXICITY_ANALYSIS = True

try:
    if USE_TOXICITY_ANALYSIS:
        from detoxify import Detoxify
        detoxify_model = Detoxify("original")
    else:
        detoxify_model = None
except Exception as e:
    print(f"[!] Detoxify could not be loaded: {e}")
    print("[!] Continuing without toxicity analysis.")
    detoxify_model = None


sentiment_analyzer = SentimentIntensityAnalyzer()


# -------------------- Helper Functions --------------------

def safe_filename_timestamp():
    """
    Creates a Windows-safe timestamp for filenames.
    Normal ISO timestamps contain ':' which can cause issues on Windows.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def clean_text(text):
    """
    Basic text cleanup for NLP.
    Keeps the original text unchanged in exports,
    but uses this cleaned version for analysis.
    """
    if not text:
        return ""

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_sentiment_label(compound_score):
    """
    Converts VADER compound score into a simple human-readable label.
    """
    if compound_score >= 0.05:
        return "positive"
    elif compound_score <= -0.05:
        return "negative"
    else:
        return "neutral"


def detect_topics(text, max_keywords=5):
    """
    Extracts simple TF-IDF keywords from a single text item.

    Note:
    TF-IDF works best across many documents, but this still gives useful
    quick keywords for a single Reddit comment/post.
    """
    cleaned = clean_text(text)

    if not cleaned or len(cleaned.split()) < 3:
        return []

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=20,
            ngram_range=(1, 2)
        )

        tfidf_matrix = vectorizer.fit_transform([cleaned])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]

        keyword_scores = list(zip(feature_names, scores))
        keyword_scores = sorted(keyword_scores, key=lambda x: x[1], reverse=True)

        keywords = [
            keyword for keyword, score in keyword_scores[:max_keywords]
            if score > 0
        ]

        return keywords

    except ValueError:
        return []


def analyze_toxicity(text):
    """
    Runs Detoxify toxicity analysis.

    Returns empty/default values if Detoxify is unavailable.
    """
    if not detoxify_model:
        return {
            "toxicity": None,
            "severe_toxicity": None,
            "obscene": None,
            "threat": None,
            "insult": None,
            "identity_attack": None
        }

    cleaned = clean_text(text)

    if not cleaned:
        return {
            "toxicity": None,
            "severe_toxicity": None,
            "obscene": None,
            "threat": None,
            "insult": None,
            "identity_attack": None
        }

    try:
        result = detoxify_model.predict(cleaned)

        return {
            "toxicity": round(float(result.get("toxicity", 0)), 4),
            "severe_toxicity": round(float(result.get("severe_toxicity", 0)), 4),
            "obscene": round(float(result.get("obscene", 0)), 4),
            "threat": round(float(result.get("threat", 0)), 4),
            "insult": round(float(result.get("insult", 0)), 4),
            "identity_attack": round(float(result.get("identity_attack", 0)), 4)
        }

    except Exception as e:
        print(f"[!] Toxicity analysis failed: {e}")
        return {
            "toxicity": None,
            "severe_toxicity": None,
            "obscene": None,
            "threat": None,
            "insult": None,
            "identity_attack": None
        }


def analyze_text(text):
    """
    Main NLP analysis function.

    Adds:
    - word count
    - sentiment scores
    - sentiment label
    - topic keywords
    - toxicity scores
    """
    cleaned = clean_text(text)
    words = cleaned.split()

    sentiment_scores = sentiment_analyzer.polarity_scores(cleaned)
    compound = sentiment_scores["compound"]

    toxicity_scores = analyze_toxicity(cleaned)

    return {
        "word_count": len(words),

        "sentiment_label": get_sentiment_label(compound),
        "sentiment_compound": compound,
        "sentiment_positive": sentiment_scores["pos"],
        "sentiment_neutral": sentiment_scores["neu"],
        "sentiment_negative": sentiment_scores["neg"],

        "topic_keywords": detect_topics(cleaned),

        "toxicity": toxicity_scores["toxicity"],
        "severe_toxicity": toxicity_scores["severe_toxicity"],
        "obscene": toxicity_scores["obscene"],
        "threat": toxicity_scores["threat"],
        "insult": toxicity_scores["insult"],
        "identity_attack": toxicity_scores["identity_attack"]
    }


def fetch_json(url, retries=3):
    headers = {"User-Agent": "RedSearchScript by u/yourusername"}

    for attempt in range(retries):
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()

        elif response.status_code == 429:
            print("[!] Rate limited. Waiting before retry...")
            time.sleep(2 + attempt * 2)

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
    """
    Converts raw Reddit JSON into a clean structured format
    and attaches NLP analysis metadata.
    """
    created_utc = item.get("created_utc", 0)

    if item_type == "comment":
        text = item.get("body") or ""
        title = ""
    else:
        title = item.get("title") or ""
        selftext = item.get("selftext") or ""
        text = f"{title}\n{selftext}".strip()

    nlp_data = analyze_text(text)

    return {
        "username": username,
        "type": item_type,
        "subreddit": item.get("subreddit", ""),
        "title": title,
        "text": text,
        "permalink": "https://www.reddit.com" + item.get("permalink", ""),
        "score": item.get("score", 0),
        "created_utc": created_utc,
        "created_datetime": datetime.fromtimestamp(created_utc, timezone.utc).isoformat(),
        "source": "reddit_json",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),

        # NLP metadata
        "word_count": nlp_data["word_count"],
        "sentiment_label": nlp_data["sentiment_label"],
        "sentiment_compound": nlp_data["sentiment_compound"],
        "sentiment_positive": nlp_data["sentiment_positive"],
        "sentiment_neutral": nlp_data["sentiment_neutral"],
        "sentiment_negative": nlp_data["sentiment_negative"],
        "topic_keywords": ", ".join(nlp_data["topic_keywords"]),

        # Toxicity metadata
        "toxicity": nlp_data["toxicity"],
        "severe_toxicity": nlp_data["severe_toxicity"],
        "obscene": nlp_data["obscene"],
        "threat": nlp_data["threat"],
        "insult": nlp_data["insult"],
        "identity_attack": nlp_data["identity_attack"]
    }


def save_to_csv(results, username):
    os.makedirs("data/csv", exist_ok=True)
    filename = f"data/csv/{username}_{safe_filename_timestamp()}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"[+] CSV saved: {filename}")


def save_to_json(results, username):
    os.makedirs("data/json", exist_ok=True)
    filename = f"data/json/{username}_{safe_filename_timestamp()}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"[+] JSON saved: {filename}")


def save_to_txt(results, username):
    os.makedirs("data/txt", exist_ok=True)
    filename = f"data/txt/{username}_{safe_filename_timestamp()}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        for item in results:
            f.write(f"Username: {item['username']}\n")
            f.write(f"Type: {item['type']}\n")
            f.write(f"Subreddit: r/{item['subreddit']}\n")
            f.write(f"Score: {item['score']}\n")
            f.write(f"Created: {item['created_datetime']}\n")
            f.write(f"Link: {item['permalink']}\n")
            f.write(f"Sentiment: {item['sentiment_label']} ({item['sentiment_compound']})\n")
            f.write(f"Word count: {item['word_count']}\n")
            f.write(f"Topics: {item['topic_keywords']}\n")
            f.write(f"Toxicity: {item['toxicity']}\n")
            f.write("\nText:\n")
            f.write(item["text"])
            f.write("\n")
            f.write("-" * 80)
            f.write("\n\n")

    print(f"[+] TXT saved: {filename}")


def print_nlp_summary(results):
    """
    Prints a simple summary after analysis.
    """
    if not results:
        return

    sentiment_counts = {
        "positive": 0,
        "neutral": 0,
        "negative": 0
    }

    total_words = 0
    toxicity_values = []

    for item in results:
        sentiment_counts[item["sentiment_label"]] += 1
        total_words += item["word_count"]

        if item["toxicity"] is not None:
            toxicity_values.append(item["toxicity"])

    average_words = total_words / len(results)

    if toxicity_values:
        average_toxicity = sum(toxicity_values) / len(toxicity_values)
    else:
        average_toxicity = None

    print("\nNLP Summary")
    print("-" * 60)
    print(f"Total analyzed items: {len(results)}")
    print(f"Average word count: {average_words:.2f}")
    print(f"Positive items: {sentiment_counts['positive']}")
    print(f"Neutral items: {sentiment_counts['neutral']}")
    print(f"Negative items: {sentiment_counts['negative']}")

    if average_toxicity is not None:
        print(f"Average toxicity: {average_toxicity:.4f}")
    else:
        print("Average toxicity: not available")

    print("-" * 60)


def save_results(results, username):
    """
    Saves all export formats in one place.
    """
    if not results:
        print("No data to save.")
        return

    save_to_csv(results, username)
    save_to_json(results, username)
    save_to_txt(results, username)


# -------------------- Main Program --------------------

def main():
    print("RedSearch")
    print("=" * 60)
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

    if not username:
        print("Username cannot be empty.")
        return

    # Google search link
    google_query = urllib.parse.quote(f'site:reddit.com "u/{username}"')
    print(f"\nGoogle search link:\nhttps://www.google.com/search?q={google_query}\n")

    comments = fetch_user_comments(username, comment_limit, paginate)
    posts = []

    print(f"\nComments by u/{username}:\n")

    for c in comments:
        print(f"u/{username} in r/{c.get('subreddit', '')}: {c.get('body', '')}")
        print(f"Link: https://www.reddit.com{c.get('permalink', '')}")
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

            print(f"u/{username} in r/{p.get('subreddit', '')}: {text}")
            print(f"Link: https://www.reddit.com{p.get('permalink', '')}")
            print("-" * 60)

    # Save structured results with NLP
    all_results = []

    print("\n[+] Normalizing and analyzing comments...")

    for c in comments:
        all_results.append(normalize_item(c, "comment", username))

    print("[+] Normalizing and analyzing posts...")

    for p in posts:
        all_results.append(normalize_item(p, "post", username))

    if all_results:
        print_nlp_summary(all_results)
        save_results(all_results, username)
    else:
        print("No data to save.")


if __name__ == "__main__":
    main()