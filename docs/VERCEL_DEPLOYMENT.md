# Vercel Deployment Guide for Source2Social

This guide will walk you through deploying your Source2Social Flask application to Vercel.

## Important Note About Vercel

⚠️ **Vercel is a serverless platform**, which means:
- Each request runs in a separate container
- No persistent file storage between requests
- SQLite database will be reset on each deployment
- Perfect for stateless APIs, but limited for apps requiring persistent data

For production use with persistent data, consider Railway, Heroku, or DigitalOcean instead.

## Prerequisites

- A Vercel account (sign up at [vercel.com](https://vercel.com))
- Your project code in a Git repository (GitHub, GitLab, or Bitbucket)
- Environment variables ready for configuration

## Step 1: Prepare Your Application

### 1.1 Vercel Configuration (Already Created)
The `vercel.json` file is configured with:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "PYTHON_VERSION": "3.11"
  }
}
```

### 1.2 App Configuration (Already Updated)
- Created `wsgi.py` as the WSGI entry point for Vercel
- Modified `app.py` to export the Flask app for Vercel
- Updated database path to use `/tmp` directory for Vercel
- Removed gunicorn from requirements (Vercel handles WSGI)
- Configured Flask templates to work with Vercel's serverless environment

## Step 2: Deploy to Vercel

### 2.1 Connect Your Repository

1. **Login to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with your GitHub/GitLab account

2. **Import Project**
   - Click "New Project"
   - Import your `sc2sm` repository
   - Vercel will auto-detect it's a Python Flask app

3. **Configure Build Settings**
   - Framework Preset: "Other"
   - Build Command: Leave empty (Vercel auto-detects)
   - Output Directory: Leave empty
   - Install Command: `pip install -r requirements.txt`

### 2.2 Set Environment Variables

In your Vercel project dashboard, go to "Settings" → "Environment Variables" and add:

#### Required Variables:
```env
SECRET_KEY=your-production-secret-key-here
VERCEL=1
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
X_REDIRECT_URI=https://your-app-name.vercel.app/oauth/x/callback
```

#### Database Configuration:
```env
DATABASE_PATH=/tmp/sc2sm.db
```

### 2.3 Deploy

1. Click "Deploy"
2. Vercel will build and deploy your application
3. You'll get a URL like: `https://your-app-name.vercel.app`

## Step 3: Configure GitHub Webhook

### 3.1 Get Your Vercel URL

After deployment, Vercel will provide you with a URL like:
```
https://your-app-name.vercel.app
```

### 3.2 Configure GitHub Webhook

1. Go to your GitHub repository
2. Navigate to "Settings" → "Webhooks"
3. Click "Add webhook"
4. Configure:
   - **Payload URL**: `https://your-app-name.vercel.app/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: Use the same value as `GITHUB_WEBHOOK_SECRET`
   - **Events**: Select "Just the push event"
   - **Active**: Check this box

5. Click "Add webhook"

## Step 4: Test Your Deployment

### 4.1 Health Check
Visit: `https://your-app-name.vercel.app/health`

You should see:
```json
{
  "status": "healthy",
  "service": "source2social",
  "version": "1.0.0"
}
```

### 4.2 Dashboard
Visit: `https://your-app-name.vercel.app`

You should see your dashboard with:
- **Header**: Source2Social logo and navigation
- **OAuth Status**: X (Twitter) connection status
- **Posts Section**: Will show generated posts from commits
- **Quick Stats**: Total posts, published, and pending counts
- **Getting Started**: Instructions if no posts exist yet

The frontend includes:
- Responsive design with modern UI
- Real-time OAuth status checking
- Post editing and publishing functionality
- Character count for Twitter posts
- Flash messages for user feedback

### 4.3 Test Webhook
Make a commit to your repository and check if:
1. The webhook is triggered (check GitHub webhook logs)
2. A new post appears in your dashboard
3. Vercel function logs show the webhook processing

## Step 5: Limitations and Workarounds

### 5.1 Database Persistence Issue

**Problem**: SQLite database resets on each deployment/request.

**Solutions**:
1. **Use External Database**: 
   - PostgreSQL (Vercel Postgres, Supabase, PlanetScale)
   - MongoDB Atlas
   - Firebase Firestore

2. **Use Vercel KV** (Redis):
   ```python
   # Example with Vercel KV
   import redis
   r = redis.from_url(os.getenv("KV_URL"))
   ```

3. **Use External Storage**:
   - Store data in GitHub Gists
   - Use Airtable API
   - Use Notion API

### 5.2 Session Storage Issue

**Problem**: Sessions don't persist between requests.

**Solution**: Use external session storage or stateless authentication.

### 5.3 File Upload Issue

**Problem**: No persistent file storage.

**Solution**: Use external storage services (AWS S3, Cloudinary, etc.).

## Step 6: Production Considerations

### 6.1 Database Migration Example

Here's how to migrate to Vercel Postgres:

```python
# Install: pip install psycopg2-binary
import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(os.getenv("POSTGRES_URL"))

# Update your DatabaseManager class to use PostgreSQL
class DatabaseManager:
    def __init__(self):
        self.conn = get_db_connection()
    
    def init_database(self):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id SERIAL PRIMARY KEY,
                    repository_name TEXT NOT NULL,
                    commit_sha TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    commit_message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    files_changed TEXT NOT NULL,
                    generated_post TEXT NOT NULL,
                    edited_post TEXT,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted_at TIMESTAMP,
                    platform TEXT DEFAULT 'twitter'
                )
            ''')
            self.conn.commit()
```

### 6.2 Environment Variables for Production

Add to your Vercel environment variables:
```env
POSTGRES_URL=your_postgres_connection_string
KV_URL=your_vercel_kv_url
```

## Step 7: Monitoring and Debugging

### 7.1 Vercel Dashboard
- Monitor function executions
- Check logs for errors
- Monitor performance metrics

### 7.2 Function Logs
Access logs through:
- Vercel dashboard → "Functions" → Click on function → "Logs"
- Or use Vercel CLI: `vercel logs`

### 7.3 Local Development with Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Link to your project
vercel link

# Run locally
vercel dev
```

## Troubleshooting

### Common Issues:

1. **Function Timeout**
   - Vercel has a 10-second timeout for Hobby plan
   - Upgrade to Pro for longer timeouts
   - Optimize your code for faster execution

2. **Database Connection Issues**
   - Ensure external database is accessible
   - Check connection strings and credentials
   - Use connection pooling for better performance

3. **Environment Variables Not Working**
   - Verify variables are set in Vercel dashboard
   - Check variable names match exactly
   - Redeploy after adding new variables

4. **Import Errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility
   - Use specific package versions

### Debug Commands:

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Link to your project
vercel link

# View logs
vercel logs

# Run locally
vercel dev

# Deploy preview
vercel --prod
```

## Alternative: Hybrid Approach

Consider using Vercel for the web interface and a separate service for data persistence:

1. **Frontend**: Deploy Flask app to Vercel
2. **API**: Use Vercel for webhook processing
3. **Database**: Use external service (Railway, Supabase, etc.)
4. **Storage**: Use external storage service

## Cost Considerations

Vercel offers:
- **Hobby Plan**: Free with limitations
- **Pro Plan**: $20/month for production apps
- **Team Plans**: For collaborative projects

Monitor your usage in the Vercel dashboard to optimize costs.

## Next Steps

1. **Migrate to External Database**: Set up PostgreSQL or MongoDB
2. **Implement Caching**: Use Vercel KV for session storage
3. **Add Monitoring**: Set up error tracking with Sentry
4. **Optimize Performance**: Implement connection pooling and caching

Your Source2Social app is now deployed on Vercel! 🚀

**Note**: Due to Vercel's serverless nature, consider this deployment as a proof-of-concept. For production use with persistent data, consider Railway or other platforms that support persistent storage.
