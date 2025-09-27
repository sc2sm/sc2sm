# GitHub Webhook Setup Guide

## Overview

This guide walks you through setting up GitHub webhooks to automatically send commit data to Source2Social, enabling automatic post generation from your development activity.

## Prerequisites

- GitHub repository with admin access
- Source2Social application deployed and accessible
- GitHub webhook secret configured in your Source2Social environment

## Step-by-Step Setup

### 1. Access Repository Settings

1. Navigate to your GitHub repository
2. Click on the **Settings** tab (requires admin access)
3. In the left sidebar, click **Webhooks**
4. Click **Add webhook**

### 2. Configure Webhook Settings

#### Basic Configuration

- **Payload URL**: `https://your-domain.com/webhook/github`
  - Replace `your-domain.com` with your actual Source2Social domain
  - For local development: `http://localhost:8000/webhook/github`
  - For Vercel deployment: `https://your-app.vercel.app/webhook/github`

- **Content type**: Select `application/json`

- **Secret**: Enter your webhook secret
  - This should match the `GITHUB_WEBHOOK_SECRET` in your Source2Social environment
  - Generate a secure random string if you don't have one

#### Event Selection

- **Which events would you like to trigger this webhook?**
  - Select **"Just the push event"** for basic functionality
  - This will trigger on every push to any branch

- **Active**: Ensure this checkbox is checked

### 3. Advanced Configuration (Optional)

#### Branch Filtering

If you only want to generate posts for specific branches:

1. In the webhook settings, scroll down to **"Which events would you like to trigger this webhook?"**
2. Select **"Let me select individual events"**
3. Check **"Pushes"**
4. In the **Branch filter** section, specify:
   - `main` - Only main branch pushes
   - `main,master` - Both main and master branches
   - `feature/*` - All feature branches

#### File Path Filtering

To ignore certain file types or directories:

1. In the webhook settings, scroll to **"Which events would you like to trigger this webhook?"**
2. Select **"Let me select individual events"**
3. Check **"Pushes"**
4. In the **File filter** section, add patterns to ignore:
   - `*.md` - Ignore markdown files
   - `docs/*` - Ignore docs directory
   - `*.log` - Ignore log files

### 4. Test the Webhook

#### Create Test Webhook

1. Click **Add webhook** to save your configuration
2. GitHub will immediately send a test payload to verify the URL is accessible
3. Check the **Recent Deliveries** section to see if the test was successful

#### Verify in Source2Social

1. Navigate to your Source2Social dashboard
2. Check the **Recent Posts** section
3. Make a test commit to your repository
4. Verify a post appears in the dashboard

### 5. Troubleshooting Webhook Delivery

#### Check Recent Deliveries

1. In your webhook settings, click on the webhook you created
2. Scroll down to **Recent Deliveries**
3. Click on individual delivery attempts to see:
   - Response status code
   - Response body
   - Request payload
   - Delivery time

#### Common Issues

**404 Not Found**
- Verify the webhook URL is correct
- Ensure Source2Social is running and accessible
- Check that the `/webhook/github` endpoint exists

**401 Unauthorized**
- Verify the webhook secret matches your configuration
- Check that `GITHUB_WEBHOOK_SECRET` is set correctly

**500 Internal Server Error**
- Check Source2Social application logs
- Verify database connectivity
- Ensure all required environment variables are set

**Timeout**
- Check network connectivity between GitHub and your server
- Verify server response time is under GitHub's timeout limit
- Consider using a reverse proxy for better performance

## Security Considerations

### Webhook Secret

The webhook secret is crucial for security:

1. **Generate a Strong Secret**
   ```bash
   # Generate a random 32-character secret
   openssl rand -hex 16
   ```

2. **Store Securely**
   - Never commit the secret to version control
   - Use environment variables or secret management services
   - Rotate the secret periodically

3. **Verify in Source2Social**
   - Source2Social validates the webhook signature
   - Rejects requests with invalid signatures
   - Logs security violations

### Network Security

- **Use HTTPS**: Always use HTTPS for webhook URLs in production
- **Firewall Rules**: Restrict access to webhook endpoints
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **IP Whitelisting**: Consider whitelisting GitHub's IP ranges

## Multiple Repository Setup

### Setting Up Multiple Repositories

If you want to generate posts from multiple repositories:

1. **Repeat the Setup Process**
   - Go to each repository's Settings → Webhooks
   - Add webhook with the same configuration
   - Use the same webhook secret for consistency

2. **Repository Identification**
   - Source2Social automatically identifies the source repository
   - Posts include repository information
   - You can filter posts by repository in the dashboard

### Organization Webhooks

For organization-wide setup:

1. **Organization Settings**
   - Go to your GitHub organization
   - Navigate to Settings → Webhooks
   - Add webhook for the entire organization

2. **Repository Selection**
   - Choose which repositories to include
   - Use branch and file filters as needed
   - Consider different webhook secrets for different teams

## Webhook Payload Structure

Understanding the webhook payload helps with debugging and customization:

```json
{
  "ref": "refs/heads/main",
  "before": "abc123...",
  "after": "def456...",
  "repository": {
    "name": "my-repo",
    "full_name": "username/my-repo",
    "html_url": "https://github.com/username/my-repo"
  },
  "pusher": {
    "name": "username",
    "email": "user@example.com"
  },
  "commits": [
    {
      "id": "def456...",
      "message": "feat: add user authentication",
      "timestamp": "2024-01-15T10:30:00Z",
      "author": {
        "name": "John Doe",
        "email": "john@example.com"
      },
      "added": ["src/auth.py"],
      "modified": ["README.md"],
      "removed": []
    }
  ]
}
```

## Advanced Configuration

### Custom Webhook Endpoints

If you need custom webhook processing:

1. **Create Custom Endpoint**
   ```python
   @app.route('/webhook/github/custom', methods=['POST'])
   def custom_webhook():
       # Custom processing logic
       pass
   ```

2. **Configure GitHub Webhook**
   - Use your custom endpoint URL
   - Apply the same security measures

### Webhook Retry Configuration

GitHub automatically retries failed webhook deliveries:

- **Retry Schedule**: 1, 5, 10, 30, 60, 120, 300, 600, 1800 seconds
- **Max Retries**: 5 attempts
- **Timeout**: 10 seconds per attempt

Ensure your endpoint can handle retries gracefully.

## Monitoring and Maintenance

### Webhook Health Monitoring

1. **Check Delivery Status**
   - Monitor Recent Deliveries regularly
   - Set up alerts for failed deliveries
   - Track response times

2. **Application Monitoring**
   - Monitor Source2Social application logs
   - Set up health checks for webhook endpoints
   - Track webhook processing performance

### Maintenance Tasks

1. **Regular Security Review**
   - Rotate webhook secrets periodically
   - Review webhook permissions
   - Audit webhook access logs

2. **Performance Optimization**
   - Monitor webhook processing time
   - Optimize database queries
   - Scale infrastructure as needed

## Testing Webhook Integration

### Manual Testing

1. **Create Test Commit**
   ```bash
   git commit -m "test: verify webhook integration"
   git push origin main
   ```

2. **Check Dashboard**
   - Verify post appears in Source2Social dashboard
   - Check post content accuracy
   - Test editing and publishing

### Automated Testing

Create test scripts to verify webhook functionality:

```python
import requests
import json

def test_webhook():
    url = "https://your-domain.com/webhook/github"
    payload = {
        "ref": "refs/heads/main",
        "commits": [{
            "message": "test: automated webhook test",
            "author": {"name": "Test User"}
        }]
    }
    
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    print("Webhook test passed!")

if __name__ == "__main__":
    test_webhook()
```

## Troubleshooting Checklist

- [ ] Webhook URL is correct and accessible
- [ ] Webhook secret matches configuration
- [ ] Source2Social application is running
- [ ] Database is accessible and writable
- [ ] All required environment variables are set
- [ ] Network connectivity between GitHub and server
- [ ] Webhook events are configured correctly
- [ ] Branch and file filters are appropriate
- [ ] Recent deliveries show successful responses
- [ ] Source2Social logs show webhook processing

## Next Steps

After setting up your webhook:

1. **Configure Social Media Integration** - See [Social Media Integration Guide](./SOCIAL_MEDIA_INTEGRATION.md)
2. **Customize Post Templates** - Adjust how commits are transformed into posts
3. **Set Up Monitoring** - Monitor webhook health and post generation
4. **Test End-to-End Flow** - Verify complete workflow from commit to social post

For additional help, see the [Troubleshooting Guide](./TROUBLESHOOTING.md) or check the [User Guide](./USER_GUIDE.md).
