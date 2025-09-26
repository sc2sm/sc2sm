"""
Twitter API service for social media posting.
"""
import tweepy
from typing import Dict, List, Optional, Any
from models import Post, User
from app import db

class TwitterService:
    """Service for interacting with Twitter API."""
    
    def __init__(self, api_key: str = None, api_secret: str = None, 
                 access_token: str = None, access_token_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        
        self.client = None
        self.api = None
        
        if all([api_key, api_secret, access_token, access_token_secret]):
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Twitter API client."""
        try:
            # Initialize OAuth 1.0a User Context
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )
            
            # Initialize API v1.1 (for some operations)
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Initialize API v2 client
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
        except Exception as e:
            print(f"Error initializing Twitter client: {e}")
            self.client = None
            self.api = None
    
    def verify_credentials(self) -> bool:
        """Verify Twitter API credentials."""
        if not self.client:
            return False
        
        try:
            user = self.client.get_me()
            return user.data is not None
        except Exception as e:
            print(f"Error verifying Twitter credentials: {e}")
            return False
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user information from Twitter."""
        if not self.client:
            return None
        
        try:
            user = self.client.get_me(user_fields=['public_metrics', 'verified'])
            if user.data:
                return {
                    'id': user.data.id,
                    'username': user.data.username,
                    'name': user.data.name,
                    'verified': getattr(user.data, 'verified', False),
                    'followers_count': getattr(user.data.public_metrics, 'followers_count', 0),
                    'following_count': getattr(user.data.public_metrics, 'following_count', 0),
                    'tweet_count': getattr(user.data.public_metrics, 'tweet_count', 0)
                }
        except Exception as e:
            print(f"Error fetching Twitter user info: {e}")
        
        return None
    
    def post_tweet(self, content: str, media_ids: List[str] = None) -> Optional[Dict[str, Any]]:
        """Post a tweet to Twitter."""
        if not self.client:
            return None
        
        try:
            # Ensure content doesn't exceed character limit
            if len(content) > 280:
                content = content[:277] + "..."
            
            # Post tweet
            response = self.client.create_tweet(
                text=content,
                media_ids=media_ids
            )
            
            if response.data:
                return {
                    'id': response.data['id'],
                    'text': content,
                    'created_at': response.data.get('created_at')
                }
                
        except Exception as e:
            print(f"Error posting tweet: {e}")
        
        return None
    
    def get_tweet(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Get tweet information by ID."""
        if not self.client:
            return None
        
        try:
            tweet = self.client.get_tweet(
                tweet_id,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations']
            )
            
            if tweet.data:
                return {
                    'id': tweet.data.id,
                    'text': tweet.data.text,
                    'created_at': tweet.data.created_at,
                    'public_metrics': tweet.data.public_metrics
                }
                
        except Exception as e:
            print(f"Error fetching tweet {tweet_id}: {e}")
        
        return None
    
    def update_tweet_metrics(self, post: Post) -> bool:
        """Update post metrics from Twitter."""
        if not post.platform_post_id or not self.client:
            return False
        
        try:
            tweet = self.get_tweet(post.platform_post_id)
            if tweet and tweet.get('public_metrics'):
                metrics = tweet['public_metrics']
                post.likes_count = metrics.get('like_count', 0)
                post.retweets_count = metrics.get('retweet_count', 0)
                post.comments_count = metrics.get('reply_count', 0)
                post.views_count = metrics.get('impression_count', 0)
                
                db.session.commit()
                return True
                
        except Exception as e:
            print(f"Error updating tweet metrics: {e}")
        
        return False
    
    def delete_tweet(self, tweet_id: str) -> bool:
        """Delete a tweet from Twitter."""
        if not self.client:
            return False
        
        try:
            response = self.client.delete_tweet(tweet_id)
            return response.data.get('deleted', False)
        except Exception as e:
            print(f"Error deleting tweet {tweet_id}: {e}")
            return False
    
    def upload_media(self, media_path: str) -> Optional[str]:
        """Upload media to Twitter and return media ID."""
        if not self.api:
            return None
        
        try:
            media = self.api.media_upload(media_path)
            return media.media_id_string
        except Exception as e:
            print(f"Error uploading media: {e}")
            return None
    
    def get_user_timeline(self, user_id: str = None, count: int = 20) -> List[Dict[str, Any]]:
        """Get user's timeline tweets."""
        if not self.client:
            return []
        
        try:
            if not user_id:
                # Get authenticated user's timeline
                tweets = self.client.get_home_timeline(
                    max_results=count,
                    tweet_fields=['created_at', 'public_metrics']
                )
            else:
                # Get specific user's timeline
                tweets = self.client.get_users_tweets(
                    id=user_id,
                    max_results=count,
                    tweet_fields=['created_at', 'public_metrics']
                )
            
            if tweets.data:
                return [
                    {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at,
                        'public_metrics': tweet.public_metrics
                    }
                    for tweet in tweets.data
                ]
                
        except Exception as e:
            print(f"Error fetching timeline: {e}")
        
        return []
    
    def search_tweets(self, query: str, count: int = 20) -> List[Dict[str, Any]]:
        """Search for tweets."""
        if not self.client:
            return []
        
        try:
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=count,
                tweet_fields=['created_at', 'public_metrics', 'author_id']
            )
            
            if tweets.data:
                return [
                    {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at,
                        'public_metrics': tweet.public_metrics,
                        'author_id': tweet.author_id
                    }
                    for tweet in tweets.data
                ]
                
        except Exception as e:
            print(f"Error searching tweets: {e}")
        
        return []
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get Twitter API rate limit status."""
        if not self.api:
            return {}
        
        try:
            rate_limits = self.api.get_rate_limit_status()
            return {
                'remaining': rate_limits.get('remaining', 0),
                'limit': rate_limits.get('limit', 0),
                'reset': rate_limits.get('reset', 0)
            }
        except Exception as e:
            print(f"Error fetching rate limit status: {e}")
            return {}
    
    def format_commit_post(self, commit_message: str, repository_name: str, 
                          commit_url: str, tone: str = 'professional') -> str:
        """Format a commit message into a Twitter post."""
        # Clean up commit message
        clean_message = commit_message.strip()
        
        # Remove common prefixes
        prefixes_to_remove = ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:']
        for prefix in prefixes_to_remove:
            if clean_message.lower().startswith(prefix):
                clean_message = clean_message[len(prefix):].strip()
        
        # Truncate if too long
        max_length = 200  # Leave room for hashtags and URL
        if len(clean_message) > max_length:
            clean_message = clean_message[:max_length-3] + "..."
        
        # Format based on tone
        if tone == 'casual':
            post = f"Just pushed some code to {repository_name}! 🚀\n\n{clean_message}"
        elif tone == 'technical':
            post = f"Code update in {repository_name}:\n\n{clean_message}"
        else:  # professional
            post = f"Latest update to {repository_name}:\n\n{clean_message}"
        
        # Add URL if there's space
        if len(post) + len(commit_url) + 1 <= 280:
            post += f"\n{commit_url}"
        
        # Add hashtags if there's space
        hashtags = ["#coding", "#github", "#opensource"]
        for hashtag in hashtags:
            if len(post) + len(hashtag) + 1 <= 280:
                post += f" {hashtag}"
            else:
                break
        
        return post
