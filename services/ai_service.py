"""
AI service for content generation and processing.
"""
import openai
import anthropic
from typing import Dict, List, Optional, Any
from models import Commit, Post

class AIService:
    """Service for AI-powered content generation."""
    
    def __init__(self, openai_api_key: str = None, anthropic_api_key: str = None):
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        
        # Initialize OpenAI client
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai
        else:
            self.openai_client = None
        
        # Initialize Anthropic client
        if anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        else:
            self.anthropic_client = None
    
    def generate_commit_post(self, commit: Commit, tone: str = 'professional', 
                           platform: str = 'twitter') -> Optional[str]:
        """Generate a social media post from a commit message."""
        if not self.openai_client and not self.anthropic_client:
            return self._fallback_post_generation(commit, tone, platform)
        
        # Prepare the prompt
        prompt = self._create_commit_prompt(commit, tone, platform)
        
        # Try OpenAI first, then Anthropic
        if self.openai_client:
            return self._generate_with_openai(prompt, tone, platform)
        elif self.anthropic_client:
            return self._generate_with_anthropic(prompt, tone, platform)
        
        return self._fallback_post_generation(commit, tone, platform)
    
    def _create_commit_prompt(self, commit: Commit, tone: str, platform: str) -> str:
        """Create a prompt for AI content generation."""
        tone_descriptions = {
            'professional': 'professional and business-like',
            'casual': 'casual and friendly',
            'technical': 'technical and detailed'
        }
        
        platform_limits = {
            'twitter': '280 characters',
            'linkedin': '3000 characters',
            'facebook': '63206 characters'
        }
        
        tone_desc = tone_descriptions.get(tone, 'professional')
        char_limit = platform_limits.get(platform, '280 characters')
        
        prompt = f"""
        Convert this GitHub commit message into a {tone_desc} social media post for {platform} (max {char_limit}).
        
        Commit Details:
        - Repository: {commit.repository.full_name}
        - Message: {commit.message}
        - Author: {commit.author_name}
        - Changes: +{commit.additions}/-{commit.deletions} lines, {commit.changed_files} files
        
        Requirements:
        1. Make it engaging and shareable
        2. Include relevant hashtags
        3. Keep the {tone} tone
        4. Stay within {char_limit} character limit
        5. Include a call-to-action if appropriate
        
        Generate only the post content, no additional text.
        """
        
        return prompt
    
    def _generate_with_openai(self, prompt: str, tone: str, platform: str) -> Optional[str]:
        """Generate content using OpenAI API."""
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a social media content creator who converts technical commit messages into engaging posts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating content with OpenAI: {e}")
            return None
    
    def _generate_with_anthropic(self, prompt: str, tone: str, platform: str) -> Optional[str]:
        """Generate content using Anthropic API."""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=200,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"Error generating content with Anthropic: {e}")
            return None
    
    def _fallback_post_generation(self, commit: Commit, tone: str, platform: str) -> str:
        """Fallback post generation when AI services are not available."""
        # Clean up commit message
        clean_message = commit.message.strip()
        
        # Remove common prefixes
        prefixes_to_remove = ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:']
        for prefix in prefixes_to_remove:
            if clean_message.lower().startswith(prefix):
                clean_message = clean_message[len(prefix):].strip()
        
        # Truncate if too long
        max_length = 200 if platform == 'twitter' else 500
        if len(clean_message) > max_length:
            clean_message = clean_message[:max_length-3] + "..."
        
        # Format based on tone
        if tone == 'casual':
            post = f"Just pushed some code to {commit.repository.name}! 🚀\n\n{clean_message}"
        elif tone == 'technical':
            post = f"Code update in {commit.repository.name}:\n\n{clean_message}\n\n+{commit.additions}/-{commit.deletions} lines"
        else:  # professional
            post = f"Latest update to {commit.repository.name}:\n\n{clean_message}"
        
        # Add hashtags
        hashtags = ["#coding", "#github", "#opensource"]
        if platform == 'twitter':
            hashtags.append("#dev")
        
        for hashtag in hashtags:
            if len(post) + len(hashtag) + 1 <= (280 if platform == 'twitter' else 1000):
                post += f" {hashtag}"
            else:
                break
        
        return post
    
    def improve_post_content(self, content: str, tone: str = 'professional') -> Optional[str]:
        """Improve existing post content using AI."""
        if not self.openai_client and not self.anthropic_client:
            return content
        
        prompt = f"""
        Improve this social media post to make it more engaging and {tone}:
        
        Original post: {content}
        
        Requirements:
        1. Keep the core message
        2. Make it more engaging
        3. Maintain {tone} tone
        4. Add appropriate emojis if suitable
        5. Keep it concise
        
        Return only the improved post content.
        """
        
        if self.openai_client:
            return self._generate_with_openai(prompt, tone, 'twitter')
        elif self.anthropic_client:
            return self._generate_with_anthropic(prompt, tone, 'twitter')
        
        return content
    
    def generate_hashtags(self, content: str, count: int = 5) -> List[str]:
        """Generate relevant hashtags for content."""
        if not self.openai_client and not self.anthropic_client:
            return self._fallback_hashtags(content, count)
        
        prompt = f"""
        Generate {count} relevant hashtags for this social media post:
        
        Content: {content}
        
        Requirements:
        1. Make hashtags relevant to the content
        2. Include a mix of popular and niche tags
        3. Use common programming/tech hashtags when appropriate
        4. Return only the hashtags, one per line
        
        Example format:
        #coding
        #python
        #webdev
        """
        
        if self.openai_client:
            response = self._generate_with_openai(prompt, 'professional', 'twitter')
        elif self.anthropic_client:
            response = self._generate_with_anthropic(prompt, 'professional', 'twitter')
        else:
            return self._fallback_hashtags(content, count)
        
        if response:
            hashtags = [line.strip() for line in response.split('\n') if line.strip().startswith('#')]
            return hashtags[:count]
        
        return self._fallback_hashtags(content, count)
    
    def _fallback_hashtags(self, content: str, count: int) -> List[str]:
        """Fallback hashtag generation."""
        base_hashtags = ["#coding", "#github", "#opensource", "#dev", "#tech"]
        
        # Add content-specific hashtags
        content_lower = content.lower()
        if 'fix' in content_lower or 'bug' in content_lower:
            base_hashtags.append("#bugfix")
        if 'feature' in content_lower or 'feat' in content_lower:
            base_hashtags.append("#feature")
        if 'refactor' in content_lower:
            base_hashtags.append("#refactor")
        if 'test' in content_lower:
            base_hashtags.append("#testing")
        
        return base_hashtags[:count]
    
    def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment of content."""
        # Simple sentiment analysis (can be enhanced with AI)
        positive_words = ['great', 'awesome', 'amazing', 'excellent', 'fantastic', 'love', 'best']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'worst', 'broken']
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            score = 0.7
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = 0.3
        else:
            sentiment = 'neutral'
            score = 0.5
        
        return {
            'sentiment': sentiment,
            'score': score,
            'positive_words': positive_count,
            'negative_words': negative_count
        }
    
    def extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content."""
        # Simple keyword extraction (can be enhanced with AI)
        import re
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Filter out stop words and get unique words
        keywords = list(set([word for word in words if word not in stop_words]))
        
        return keywords[:10]  # Return top 10 keywords
