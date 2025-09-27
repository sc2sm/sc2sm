#!/usr/bin/env python3
"""
Simple Twitter API test script to debug authentication issues
"""
import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

# Get credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

print("=== Twitter API Test ===")
print(f"API Key: {TWITTER_API_KEY[:10]}...{TWITTER_API_KEY[-5:]}")
print(f"API Secret: {TWITTER_API_SECRET[:10]}...{TWITTER_API_SECRET[-5:]}")
print(f"Access Token: {TWITTER_ACCESS_TOKEN[:15]}...{TWITTER_ACCESS_TOKEN[-10:]}")
print(f"Access Token Secret: {TWITTER_ACCESS_TOKEN_SECRET[:10]}...{TWITTER_ACCESS_TOKEN_SECRET[-5:]}")

try:
    # Test v1.1 API
    print("\n--- Testing Twitter API v1.1 ---")
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    print("Testing verify_credentials...")
    user = api.verify_credentials()
    print(f"✅ v1.1 Authentication successful! User: @{user.screen_name}")
    print(f"   User ID: {user.id}")
    print(f"   Account created: {user.created_at}")
    print(f"   Followers: {user.followers_count}")

    # Test posting a simple tweet
    print("\nTesting tweet posting...")
    test_tweet = "🤖 Testing Twitter API connection - timestamp: " + str(__import__('time').time())
    status = api.update_status(test_tweet)
    print(f"✅ Tweet posted successfully! ID: {status.id}")
    print(f"   Tweet URL: https://twitter.com/{status.user.screen_name}/status/{status.id}")

except tweepy.TweepyException as e:
    print(f"❌ v1.1 API failed: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"   HTTP Status: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
except Exception as e:
    print(f"❌ General error: {e}")

try:
    # Test v2 API
    print("\n--- Testing Twitter API v2 ---")
    client = tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )

    print("Testing get_me...")
    me = client.get_me()
    print(f"✅ v2 Authentication successful! User: @{me.data.username}")

    # Test posting via v2
    print("Testing v2 tweet posting...")
    test_tweet_v2 = "🚀 Testing Twitter API v2 connection - timestamp: " + str(__import__('time').time())
    response = client.create_tweet(text=test_tweet_v2)
    print(f"✅ v2 Tweet posted successfully! ID: {response.data['id']}")

except tweepy.TweepyException as e:
    print(f"❌ v2 API failed: {e}")
except Exception as e:
    print(f"❌ v2 General error: {e}")

print("\n=== Test Complete ===")