#!/usr/bin/env python3
"""
Test OpenAI integration for Source2Social
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import from app.py
sys.path.append('.')

try:
    from app import PostGenerator, CommitData

    def test_post_generation():
        """Test the post generation with a sample commit"""

        print("🧪 Testing OpenAI Post Generation")
        print("=" * 50)

        # Check if OpenAI is configured
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key or openai_key == "your_openai_api_key_here":
            print("❌ OpenAI API key not configured in .env file")
            return False

        print("✅ OpenAI API key found")

        # Create a sample commit
        sample_commit = CommitData(
            author_name="Sree Pradhip",
            commit_message="Add AI-powered social media post generation feature",
            timestamp=datetime.now().isoformat(),
            added_files=["app.py", "templates/dashboard.html", "setup_ngrok.py"],
            modified_files=["requirements.txt", "README.md"],
            removed_files=[],
            repository_name="source2social",
            branch="main",
            sha="abc123def456789"
        )

        # Generate post
        print("🤖 Generating social media post...")
        generator = PostGenerator()

        try:
            generated_post = generator.generate_post(sample_commit)

            print("\n📝 Generated Post:")
            print("-" * 30)
            print(generated_post)
            print("-" * 30)
            print(f"📊 Character count: {len(generated_post)}/280")

            if len(generated_post) <= 280:
                print("✅ Post fits Twitter character limit!")
            else:
                print("⚠️  Post exceeds Twitter character limit")

            return True

        except Exception as e:
            print(f"❌ Error generating post: {e}")
            print("💡 This might be due to OpenAI API issues or invalid key")
            return False

    if __name__ == "__main__":
        success = test_post_generation()

        if success:
            print("\n🎉 OpenAI integration is working!")
            print("🚀 Your Source2Social app is ready to generate amazing posts!")
        else:
            print("\n🔧 Please check your OpenAI configuration")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the Flask app dependencies are installed")
except Exception as e:
    print(f"❌ Unexpected error: {e}")