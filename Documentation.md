Legal and Terms of Service Disclaimer

RedSearch is a tool for accessing publicly available Reddit content only. It fetches user comments and posts that are visible to anyone on Reddit without bypassing any authentication or accessing private content.

Important Notes:

Public Content Only:

RedSearch only retrieves data from public subreddits and user profiles.

Private subreddits, restricted posts, or deleted content cannot be accessed.

Rate Limits and Responsible Use:

The tool respects Reddit’s rate limits for unauthenticated requests (~60 requests per minute).

Excessive automated requests may be flagged; use responsibly.

User-Agent Compliance:

All requests include a custom User-Agent to identify the script, following Reddit API guidelines.

Personal Use:

RedSearch is intended for personal research, reference, or analysis.

Republishing, reselling, or redistributing large volumes of Reddit content may violate Reddit’s Terms of Service.

By using RedSearch, you agree to use the tool responsibly and only for content that is publicly available on Reddit. The developers are not responsible for misuse of the tool.




This project is a hobby that was based on a random idea that I had and has probably done many times over. 


# Quick start

1. Get all the files in this repo
2. Navigate to RedSearch/src
3. python redsearch1
4. Follow the prompts

Purpose:
RedSearch0 was the first iteration of the Reddit search tool. Its main goal was to locate a Reddit user’s comments and posts by performing a Google search restricted to Reddit.

How it worked:

The program relied on Google Custom Search API.

Users entered a Reddit username, and the program constructed a search query like:


    site:reddit.com "u/<username>"

The Google API returned search results, including links, titles, and snippets.

The program displayed the results in the console, allowing the user to browse potential posts or comments.


Limitations:

The snippet was not guaranteed to be the full comment or post — it was just the portion Google indexed.

Fetching large numbers of results consumed more of the Google API quota.

Google API keys needed to be created and stored securely, adding setup complexity.

There was no direct connection to Reddit; results depended entirely on Google indexing.


So redsearch0.py is still usable but it got superceded by redsearch1.py by a wide margin. Additionally it required use of Google API and Custom Search Engine (CSE).

The Google API also had a limited number of free queries (100), after that it would cost money to do queries.


RedSearch1 was the first version that directly connected to Reddit instead of relying on Google. The goal was to fetch actual user comments, providing more accurate and reliable data.

How it worked:

Uses the Reddit JSON API via requests.

Fetches a limited number of recent comments (default 10).

Optionally fetches posts based on user input (y/n).

Each comment includes the username, subreddit, and permalink (source link).

Google search link is still provided, but the program now accesses real Reddit data.

Advantages over RedSearch0:

Provides exact user comments and posts instead of Google snippets.

Lightweight — fetches only as many items as requested.

Does not require Google API keys or quota management.

Faster for small searches and easier to run locally.


# Development Process:

Reddit API Research:

Learned that Reddit exposes JSON endpoints for users:

Comments: /user/<username>/comments.json

Posts: /user/<username>/submitted.json

Maximum 100 items per request; pagination required for more.

Python Program:

Implemented requests.get with a User-Agent header to avoid 429 errors.

Added functions fetch_user_comments() and fetch_user_posts().

Limited results to 10 comments for lightweight mode.

Output Design:

Printed username, comment body, subreddit, and a link to the original Reddit content.

Added an option for the user to decide whether to view posts.

Retained Google search link for convenience.

## Modes

RedSearch1.py offers three search modes to control how many comments and posts are fetched:

# Light Mode (Mode 1)

Fetches 10 recent comments by the specified user.

Prompts the user whether to fetch posts (y/n).

Designed for quick, lightweight searches.

# Medium Mode (Mode 2)

Fetches 30 recent comments and 30 posts automatically.

No prompts; displays all results directly.

Suitable for more thorough searches without overwhelming output.

# Max Mode (Mode 3)

Fetches all available comments and posts for the user.

Uses pagination to retrieve more than 100 items if necessary.

Ideal for comprehensive data collection.

Additional Notes:

These modes are made for ease of use, naturally they can be adjusted in the code itself if needed in the comment_limit and post_limit respectively

In all modes, a Google search link is provided to browse the user’s activity.

Output includes the username, subreddit, comment/post content, and permalink.

Max Mode can take up to several minutes depending of the amount of posts and comments the user has made 


## Updated features

- Save results as .csv and .json for possible future NLP analysis



