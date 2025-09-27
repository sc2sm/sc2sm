# Source2Social User Guide

## Table of Contents
- [Getting Started](#getting-started)
- [Dashboard Overview](#dashboard-overview)
- [Setting Up Integrations](#setting-up-integrations)
- [Managing Posts](#managing-posts)
- [Understanding Generated Content](#understanding-generated-content)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### What is Source2Social?

Source2Social (S2S) is a developer-focused tool that automatically transforms your GitHub commits into engaging social media posts. It's designed for indie hackers, startup teams, and builders-in-public who want to share their development journey without the manual effort.

### Key Benefits

- **Automated Content Creation**: Turn commits into social posts automatically
- **Build in Public**: Share your coding progress effortlessly
- **Community Engagement**: Keep your audience updated on your development
- **Time Saving**: No more manual social media posting

### Quick Start

1. **Access the Dashboard**: Navigate to `/dashboard` in your browser
2. **Set Up GitHub Webhook**: Follow the [GitHub Webhook Setup Guide](./GITHUB_WEBHOOK_SETUP.md)
3. **Configure Social Media**: Connect your Twitter/X account
4. **Start Committing**: Your commits will automatically generate posts

## Dashboard Overview

The Source2Social dashboard is your central hub for managing generated posts and configuring integrations.

### Main Sections

#### 1. Posts Management
- **Recent Posts**: View all generated posts from your commits
- **Edit Posts**: Modify generated content before publishing
- **Post Status**: Track which posts have been published
- **Scheduling**: Set up automatic or manual posting

#### 2. Integrations
- **GitHub**: Configure webhook settings and repository connections
- **Twitter/X**: Set up OAuth authentication for automatic posting
- **CodeRabbit**: Connect for enhanced code analysis and insights

#### 3. Settings
- **Post Templates**: Customize how commits are transformed into posts
- **LLM Configuration**: Adjust AI settings for content generation
- **Social Media Settings**: Configure posting preferences

### Navigation

- **Dashboard**: Main overview and post management
- **Settings**: Configuration and customization options
- **Integrations**: Third-party service connections

## Setting Up Integrations

### GitHub Integration

The GitHub integration is the core of Source2Social. It listens for webhook events from your repositories and generates posts based on commit activity.

#### Prerequisites
- GitHub repository with admin access
- Public repository (for webhook delivery)
- Source2Social application running and accessible

#### Setup Steps

1. **Navigate to GitHub Settings**
   - Go to your repository on GitHub
   - Click "Settings" → "Webhooks" → "Add webhook"

2. **Configure Webhook**
   - **Payload URL**: `https://your-domain.com/webhook/github`
   - **Content type**: `application/json`
   - **Events**: Select "Just the push event"
   - **Secret**: Use your configured webhook secret

3. **Test the Integration**
   - Make a test commit to your repository
   - Check the dashboard for generated posts
   - Verify webhook delivery in GitHub webhook settings

### Twitter/X Integration

Connect your Twitter/X account for automatic posting of generated content.

#### OAuth Setup

1. **Create Twitter App**
   - Go to [Twitter Developer Portal](https://developer.twitter.com/)
   - Create a new app with read/write permissions
   - Generate API keys and access tokens

2. **Configure in Source2Social**
   - Navigate to Settings → Social Media
   - Enter your Twitter API credentials
   - Complete OAuth flow for authentication

3. **Test Posting**
   - Generate a test post from the dashboard
   - Verify it appears on your Twitter account

### CodeRabbit Integration

CodeRabbit provides enhanced code analysis and review insights that can improve your generated posts.

#### Setup Process

1. **Get CodeRabbit API Key**
   - Sign up at [CodeRabbit](https://coderabbit.ai/)
   - Generate an API key from your dashboard

2. **Configure Integration**
   - Navigate to Settings → Integrations → CodeRabbit
   - Enter your API key
   - Test the connection

3. **Enable Enhanced Analysis**
   - Toggle enhanced analysis in post settings
   - Posts will include CodeRabbit insights when available

## Managing Posts

### Viewing Generated Posts

The dashboard displays all posts generated from your commits in chronological order. Each post shows:

- **Commit Information**: Author, message, timestamp
- **Generated Content**: The social media post text
- **Status**: Draft, Published, Scheduled, or Failed
- **Actions**: Edit, Publish, Delete, or Schedule

### Editing Posts

Before publishing, you can edit generated posts to:

- **Refine the Message**: Adjust tone, add context, or fix grammar
- **Add Hashtags**: Include relevant hashtags for better reach
- **Include Links**: Add links to your repository or related content
- **Personalize**: Add your own voice and personality

### Publishing Options

#### Manual Publishing
- Review each post individually
- Edit content before publishing
- Full control over timing and content

#### Automatic Publishing
- Posts are published immediately after generation
- Configure filters to determine which commits generate posts
- Set up approval workflows for team environments

#### Scheduled Publishing
- Queue posts for optimal posting times
- Batch multiple commits into daily/weekly summaries
- Coordinate with your social media strategy

### Post Templates

Customize how commits are transformed into social media posts:

#### Default Template
```
🚀 Just shipped: {commit_message}

{file_changes_summary}

#coding #buildinpublic #github
```

#### Custom Templates
Create templates for different types of commits:
- **Feature Commits**: Highlight new functionality
- **Bug Fixes**: Emphasize problem-solving
- **Refactoring**: Show code improvement
- **Documentation**: Promote knowledge sharing

## Understanding Generated Content

### How Posts Are Generated

Source2Social uses AI to analyze your commits and create engaging social media content:

1. **Commit Analysis**: Extracts key information from commit messages and file changes
2. **Content Generation**: Uses LLM to create engaging, developer-friendly posts
3. **Template Application**: Applies your configured templates and formatting
4. **Quality Check**: Ensures posts meet length and content requirements

### Content Types

#### Feature Announcements
- Highlight new functionality
- Include technical details
- Emphasize user benefits

#### Progress Updates
- Show development momentum
- Include metrics and achievements
- Build anticipation for releases

#### Technical Insights
- Share coding techniques
- Explain architectural decisions
- Educate your audience

#### Bug Fixes
- Demonstrate problem-solving skills
- Show attention to quality
- Build trust with users

### Content Quality

Generated posts are designed to be:
- **Engaging**: Interesting to your developer audience
- **Informative**: Provide value beyond just announcing changes
- **Authentic**: Reflect your development style and voice
- **Actionable**: Encourage interaction and engagement

## Best Practices

### Commit Message Guidelines

To get the best generated posts, follow these commit message practices:

#### Use Conventional Commits
```
feat: add user authentication system
fix: resolve memory leak in data processing
docs: update API documentation
refactor: simplify user interface components
```

#### Be Descriptive
- Explain what changed and why
- Include context about the impact
- Mention any breaking changes

#### Include Technical Details
- Reference specific technologies used
- Mention performance improvements
- Highlight security considerations

### Social Media Strategy

#### Posting Frequency
- **High Activity**: Post for significant commits only
- **Medium Activity**: Post for features and major fixes
- **Low Activity**: Post for major milestones and releases

#### Content Mix
- Balance technical posts with progress updates
- Include behind-the-scenes development insights
- Share challenges and solutions

#### Engagement
- Respond to comments and questions
- Ask for feedback on features
- Encourage community participation

### Team Collaboration

#### For Teams
- Set up approval workflows for posts
- Assign different team members to different repositories
- Coordinate posting schedules to avoid conflicts

#### For Organizations
- Establish brand guidelines for generated content
- Review and approve posts before publishing
- Monitor engagement and adjust strategy

## Troubleshooting

### Common Issues

#### Posts Not Generating

**Problem**: Commits aren't creating posts in the dashboard

**Solutions**:
1. Check webhook configuration in GitHub
2. Verify webhook secret matches your configuration
3. Check application logs for errors
4. Ensure repository is public (for webhook delivery)

#### Generated Content Quality

**Problem**: Posts don't match your style or expectations

**Solutions**:
1. Customize post templates in settings
2. Adjust LLM configuration parameters
3. Provide feedback on generated content
4. Use more descriptive commit messages

#### Social Media Posting Failures

**Problem**: Posts aren't appearing on social media

**Solutions**:
1. Verify API credentials are correct
2. Check OAuth token hasn't expired
3. Ensure app has proper permissions
4. Review rate limiting and API quotas

#### Integration Issues

**Problem**: Third-party services not working

**Solutions**:
1. Verify API keys are valid and active
2. Check service status pages
3. Review authentication flows
4. Test connections individually

### Getting Help

#### Support Resources
- **Documentation**: Check other guides in the `/docs` folder
- **GitHub Issues**: Report bugs and request features
- **Community**: Join discussions and share experiences

#### Debugging Tips
- Enable debug logging in settings
- Check application logs for detailed error messages
- Test integrations individually
- Use the health check endpoint to verify service status

### Performance Optimization

#### For High-Volume Repositories
- Use commit filtering to reduce noise
- Implement post batching for multiple commits
- Set up approval workflows for quality control

#### For Large Teams
- Configure different templates for different team members
- Use repository-specific settings
- Implement role-based access controls

---

## Next Steps

Now that you understand how to use Source2Social:

1. **Set up your first integration** following the [GitHub Webhook Setup Guide](./GITHUB_WEBHOOK_SETUP.md)
2. **Configure your social media accounts** using the [Social Media Integration Guide](./SOCIAL_MEDIA_INTEGRATION.md)
3. **Customize your post templates** to match your brand and style
4. **Start committing** and watch your social media presence grow!

For technical setup and deployment, see the [Deployment Guide](./DEPLOYMENT.md).
