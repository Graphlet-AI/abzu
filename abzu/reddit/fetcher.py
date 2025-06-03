"""Reddit data fetcher using PRAW."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import praw
from praw.models import Comment, Submission

from abzu.config import config


def save_to_jsonl(posts: List[Dict], ticker: str, output_path: Path) -> None:
    """Save posts to JSONL format matching theinformation.jsonl structure."""
    with open(output_path, "w", encoding="utf-8") as f:
        for post in posts:
            # Combine title, post text, and comments into content
            content_parts = [post["title"]]

            if post.get("selftext"):
                content_parts.append(post["selftext"])

            # Add comments if available
            comments = post.get("comments", [])
            if comments:
                content_parts.append("Comments:")
                for comment in comments[:10]:
                    if isinstance(comment, dict):
                        content_parts.append(f"- {comment.get('body', '')}")

            combined_content = " ".join(content_parts)

            # Create document matching theinformation.jsonl format
            # Use permalink for the actual Reddit post, not external URL
            reddit_url = (
                f"https://reddit.com{post['permalink']}"
                if post["permalink"].startswith("/")
                else post["permalink"]
            )

            document = {
                "title": post["title"],
                "url": reddit_url,
                "posted_at": datetime.fromtimestamp(post["created_utc"]).isoformat() + "Z",
                "content": combined_content,
                "collected_at": datetime.now().isoformat() + "Z",
            }

            f.write(json.dumps(document) + "\n")


class RedditFetcher:
    """Reddit data fetcher using PRAW."""

    def __init__(self) -> None:
        """Initialize Reddit client with credentials."""
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = config.get("reddit.user_agent", "abzu:v0.1.0 (by /u/abzu)")

        if not client_id or not client_secret:
            raise RuntimeError(
                "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be exported in your environment."
            )

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    def fetch_hot_posts(self, subreddit: str, limit: int = 10) -> List[Dict]:
        """
        Fetch hot posts from a subreddit.

        Parameters
        ----------
        subreddit : str
            Name of the subreddit
        limit : int, optional
            Number of posts to fetch, by default 10

        Returns
        -------
        List[Dict]
            List of post data dictionaries
        """
        posts = []
        sub = self.reddit.subreddit(subreddit)

        for submission in sub.hot(limit=limit):
            post_data = self._extract_submission_data(submission)
            posts.append(post_data)

        return posts

    def fetch_new_posts(self, subreddit: str, limit: int = 10) -> List[Dict]:
        """
        Fetch new posts from a subreddit.

        Parameters
        ----------
        subreddit : str
            Name of the subreddit
        limit : int, optional
            Number of posts to fetch, by default 10

        Returns
        -------
        List[Dict]
            List of post data dictionaries
        """
        posts = []
        sub = self.reddit.subreddit(subreddit)

        for submission in sub.new(limit=limit):
            post_data = self._extract_submission_data(submission)
            posts.append(post_data)

        return posts

    def fetch_top_posts(
        self, subreddit: str, time_filter: str = "day", limit: int = 10
    ) -> List[Dict]:
        """
        Fetch top posts from a subreddit.

        Parameters
        ----------
        subreddit : str
            Name of the subreddit
        time_filter : str, optional
            Time filter (hour, day, week, month, year, all), by default "day"
        limit : int, optional
            Number of posts to fetch, by default 10

        Returns
        -------
        List[Dict]
            List of post data dictionaries
        """
        posts = []
        sub = self.reddit.subreddit(subreddit)

        for submission in sub.top(time_filter=time_filter, limit=limit):
            post_data = self._extract_submission_data(submission)
            posts.append(post_data)

        return posts

    def fetch_post_with_comments(self, post_id: str, comment_limit: int = 20) -> Dict:
        """
        Fetch a specific post with its comments.

        Parameters
        ----------
        post_id : str
            Reddit post ID
        comment_limit : int, optional
            Number of top-level comments to fetch, by default 20

        Returns
        -------
        Dict
            Post data with comments
        """
        submission = self.reddit.submission(id=post_id)
        submission.comments.replace_more(limit=0)

        post_data = self._extract_submission_data(submission)
        comments = []

        for comment in submission.comments[:comment_limit]:
            if isinstance(comment, Comment):
                comment_data = self._extract_comment_data(comment)
                comments.append(comment_data)

        post_data["comments"] = comments
        return post_data

    def search_posts(
        self, query: str, subreddit: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
        """
        Search for posts.

        Parameters
        ----------
        query : str
            Search query
        subreddit : Optional[str], optional
            Specific subreddit to search in, by default None (search all)
        limit : int, optional
            Number of posts to return, by default 10

        Returns
        -------
        List[Dict]
            List of matching post data dictionaries
        """
        posts = []

        if subreddit:
            sub = self.reddit.subreddit(subreddit)
            results = sub.search(query, limit=limit)
        else:
            results = self.reddit.subreddit("all").search(query, limit=limit)

        for submission in results:
            post_data = self._extract_submission_data(submission)
            posts.append(post_data)

        return posts

    def _extract_submission_data(self, submission: Submission) -> Dict:
        """
        Extract data from a Reddit submission.

        Parameters
        ----------
        submission : Submission
            PRAW submission object

        Returns
        -------
        Dict
            Extracted submission data
        """
        return {
            "id": submission.id,
            "title": submission.title,
            "author": str(submission.author) if submission.author else "[deleted]",
            "subreddit": str(submission.subreddit),
            "score": submission.score,
            "upvote_ratio": submission.upvote_ratio,
            "num_comments": submission.num_comments,
            "created_utc": submission.created_utc,
            "url": submission.url,
            "permalink": submission.permalink,
            "selftext": submission.selftext,
            "is_self": submission.is_self,
            "link_flair_text": submission.link_flair_text,
            "post_hint": getattr(submission, "post_hint", None),
            "domain": submission.domain,
            "gilded": submission.gilded,
            "distinguished": submission.distinguished,
            "stickied": submission.stickied,
            "over_18": submission.over_18,
            "spoiler": submission.spoiler,
        }

    def fetch_ticker_posts(self, ticker: str, limit: int = 25) -> List[Dict]:
        """
        Fetch posts for a specific ticker across multiple finance subreddits.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol to search for
        limit : int, optional
            Number of posts to fetch per subreddit, by default 25

        Returns
        -------
        List[Dict]
            List of unique posts mentioning the ticker
        """
        # Finance-related subreddits
        subreddits = [
            "investing",
            "stocks",
            "ValueInvesting",
            "StockMarket",
            "wallstreetbets",
            "pennystocks",
            "options",
            "financialindependence",
            "investing_discussion",
            "smallstreetbets",
            "unusual_whales",
        ]

        all_posts = []

        for subreddit in subreddits:
            try:
                # Use search for better ticker relevance
                posts = self.search_posts(ticker, subreddit, limit)

                # Enhance posts with comments
                enhanced_posts = []
                for post in posts:
                    try:
                        detailed_post = self.fetch_post_with_comments(post["id"], comment_limit=10)
                        enhanced_posts.append(detailed_post)
                    except Exception:
                        # If can't get comments, use original post
                        enhanced_posts.append(post)

                all_posts.extend(enhanced_posts)
                print(f"Found {len(enhanced_posts)} posts in r/{subreddit}")
            except Exception as e:
                print(f"Error searching r/{subreddit}: {e}")
                continue

        # Remove duplicates based on post ID
        unique_posts = {post["id"]: post for post in all_posts}.values()
        final_posts = list(unique_posts)

        # Sort by recency first, then by score
        final_posts.sort(key=lambda x: (x["created_utc"], x["score"]), reverse=True)

        return final_posts

    def _extract_comment_data(self, comment: Comment) -> Dict:
        """
        Extract data from a Reddit comment.

        Parameters
        ----------
        comment : Comment
            PRAW comment object

        Returns
        -------
        Dict
            Extracted comment data
        """
        return {
            "id": comment.id,
            "author": str(comment.author) if comment.author else "[deleted]",
            "body": comment.body,
            "score": comment.score,
            "created_utc": comment.created_utc,
            "permalink": comment.permalink,
            "parent_id": comment.parent_id,
            "depth": comment.depth if hasattr(comment, "depth") else 0,
            "gilded": comment.gilded,
            "distinguished": comment.distinguished,
            "stickied": comment.stickied,
            "is_submitter": comment.is_submitter,
        }
