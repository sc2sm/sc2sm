# Railway Deployment Guide for Source2Social

This guide will walk you through deploying your Source2Social Flask application to Railway.

## Prerequisites

- A Railway account (sign up at [railway.app](https://railway.app))
- Your project code in a Git repository (GitHub, GitLab, or Bitbucket)
- Environment variables ready for configuration

## Step 1: Prepare Your Application

### 1.1 Update Procfile (Already Created)
The `Procfile` is already configured with:
```
web: python app.py
```

### 1.2 Railway Configuration (Already Created)
The `railway.json` file is configured with:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python app.py",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 1.3 Update Requirements (Already Done)
Added `gunicorn==21.2.0` for production WSGI server.

## Step 2: Deploy to Railway

### 2.1 Connect Your Repository

1. **Login to Railway**
   - Go to [railway.app](https://railway.app)
   - Sign in with your GitHub/GitLab account

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `sc2sm` repository

3. **Configure Deployment**
   - Railway will automatically detect it's a Python Flask app
   - It will use the `Procfile` and `railway.json` configurations

### 2.2 Set Environment Variables

In your Railway project dashboard, go to the "Variables" tab and add these environment variables:

#### Required Variables:
```env
SECRET_KEY=your-production-secret-key-here
PORT=5000
```

#### GitHub Webhook Configuration:
```env
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret_here
```

#### OpenAI Configuration (Optional):
```env
OPENAI_API_KEY=your_openai_api_key_here
```

#### Twitter/X API Configuration (Optional):
```env
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here
```

#### X OAuth Configuration (Optional):
```env
X_CLIENT_ID=your_x_client_id_here
X_CLIENT_SECRET=your_x_client_secret_here
X_REDIRECT_URI=https://your-app-name.railway.app/oauth/x/callback
```

#### Database Configuration:
```env
DATABASE_PATH=/app/data/sc2sm.db
```

### 2.3 Configure Custom Domain (Optional)

1. In your Railway project, go to "Settings"
2. Click "Domains"
3. Add your custom domain
4. Follow Railway's DNS configuration instructions

## Step 3: Configure GitHub Webhook

### 3.1 Get Your Railway URL

After deployment, Railway will provide you with a URL like:
```
https://your-app-name.railway.app
```

### 3.2 Configure GitHub Webhook

1. Go to your GitHub repository
2. Navigate to "Settings" → "Webhooks"
3. Click "Add webhook"
4. Configure:
   - **Payload URL**: `https://your-app-name.railway.app/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: Use the same value as `GITHUB_WEBHOOK_SECRET`
   - **Events**: Select "Just the push event"
   - **Active**: Check this box

5. Click "Add webhook"

## Step 4: Test Your Deployment

### 4.1 Health Check
Visit: `https://your-app-name.railway.app/health`

You should see:
```json
{
  "status": "healthy",
  "service": "source2social",
  "version": "1.0.0"
}
```

### 4.2 Dashboard
Visit: `https://your-app-name.railway.app`

You should see your dashboard with any existing posts.

### 4.3 Test Webhook
Make a commit to your repository and check if:
1. The webhook is triggered (check GitHub webhook logs)
2. A new post appears in your dashboard
3. Railway logs show the webhook processing

## Step 5: Monitor and Maintain

### 5.1 Railway Dashboard
- Monitor your app's performance in the Railway dashboard
- Check logs for any errors
- Monitor resource usage

### 5.2 Database Management
Railway provides persistent storage for your SQLite database. The database file will be stored at `/app/data/sc2sm.db`.

### 5.3 Logs
Access logs through:
- Railway dashboard → "Deployments" → Click on deployment → "View Logs"
- Or use Railway CLI: `railway logs`

## Troubleshooting

### Common Issues:

1. **App Won't Start**
   - Check Railway logs for Python errors
   - Verify all required environment variables are set
   - Ensure `requirements.txt` includes all dependencies

2. **Webhook Not Working**
   - Verify GitHub webhook URL is correct
   - Check `GITHUB_WEBHOOK_SECRET` matches in both places
   - Look at Railway logs for webhook processing errors

3. **Database Issues**
   - Ensure `DATABASE_PATH` is set correctly
   - Check file permissions in Railway logs

4. **OAuth Issues**
   - Verify `X_REDIRECT_URI` uses your Railway domain
   - Check X API credentials are correct

### Debug Commands:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Connect to your project
railway link

# View logs
railway logs

# Open shell in Railway environment
railway shell
```

## Production Considerations

### Security:
- Use strong, unique `SECRET_KEY`
- Keep API keys secure and rotate them regularly
- Enable HTTPS (Railway provides this automatically)

### Performance:
- Monitor resource usage in Railway dashboard
- Consider upgrading Railway plan if needed
- Implement proper error handling and logging

### Backup:
- Railway provides automatic backups
- Consider exporting your database periodically
- Keep your code in version control

## Cost Optimization

Railway offers:
- **Hobby Plan**: $5/month for small projects
- **Pro Plan**: $20/month for production apps
- **Team Plans**: For collaborative projects

Monitor your usage in the Railway dashboard to optimize costs.

## Next Steps

1. **Set up monitoring**: Consider adding Sentry for error tracking
2. **Implement CI/CD**: Use Railway's GitHub integration for automatic deployments
3. **Add caching**: Consider Redis for session storage
4. **Scale up**: Upgrade Railway plan as your usage grows

Your Source2Social app is now live on Railway! 🚀
