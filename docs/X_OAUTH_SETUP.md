# X OAuth Integration Setup

This document explains how to set up X (Twitter) OAuth integration for the Source2Social application.

## Prerequisites

1. **X Developer Account**: You need a Twitter/X developer account
2. **X App Registration**: Create a new app in the X Developer Portal

## X App Configuration

1. Go to [X Developer Portal](https://developer.twitter.com/)
2. Create a new app or use an existing one
3. In your app settings, configure:
   - **App permissions**: Read and Write (to post tweets)
   - **Callback URLs**: Add your callback URL (e.g., `http://localhost:5000/oauth/x/callback`)
   - **Website URL**: Your application's base URL

## Environment Variables

Add these variables to your `.env` file:

```bash
# X OAuth Configuration
X_CLIENT_ID=your_x_client_id_here
X_CLIENT_SECRET=your_x_client_secret_here
X_REDIRECT_URI=http://localhost:5000/oauth/x/callback
```

## OAuth Flow

The application provides the following OAuth endpoints:

- **`/oauth/x/authorize`**: Initiates the OAuth flow
- **`/oauth/x/callback`**: Handles the OAuth callback
- **`/oauth/x/disconnect`**: Disconnects the X account
- **`/oauth/x/status`**: Checks connection status (API endpoint)

## Database Schema

The OAuth tokens are stored in the `oauth_tokens` table:

```sql
CREATE TABLE oauth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL DEFAULT 'x',
    user_id TEXT NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type TEXT DEFAULT 'Bearer',
    expires_at TIMESTAMP,
    scope TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, user_id)
);
```

## Usage

1. **Connect Account**: Click "Connect X Account" on the dashboard
2. **Authorize**: Complete the OAuth flow on X
3. **Post Content**: Use the existing post publishing functionality
4. **Disconnect**: Use "Disconnect X Account" to remove the connection

## Token Management

- Access tokens are automatically stored in the database
- Refresh tokens are used to renew expired access tokens
- Token expiration is tracked and displayed in the UI
- Users can reconnect if tokens expire

## Security Notes

- OAuth state parameter is used to prevent CSRF attacks
- Tokens are stored securely in the database
- The application uses PKCE (Proof Key for Code Exchange) for additional security
- All OAuth flows use HTTPS in production

## Troubleshooting

### Common Issues

1. **"X_CLIENT_ID not configured"**: Make sure your environment variables are set
2. **"Invalid OAuth state"**: This usually indicates a CSRF attack or session issue
3. **"OAuth authorization failed"**: Check your callback URL configuration
4. **Token expiration**: Use the refresh token or reconnect the account

### Debug Mode

Enable debug mode to see detailed OAuth flow information:

```bash
DEBUG=True
```

## Production Deployment

For production deployment:

1. Update `X_REDIRECT_URI` to your production domain
2. Ensure HTTPS is enabled
3. Set `SECRET_KEY` to a secure random value
4. Configure proper database backup for token storage
