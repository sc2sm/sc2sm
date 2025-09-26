# Source2Social 🛠️➡️📣

Source2Social is a lightweight developer-focused tool that turns your GitHub commits into shareable social media updates.

Ideal for indie hackers, startup teams, and builders-in-public, it captures coding progress and broadcasts your momentum — automatically.

## 🚀 Why Source2Social?

- Celebrate your build journey without extra effort
- Share what you’re shipping — straight from your source control
- Engage your community with real-time progress updates
- Reduce friction between product and visibility

## 🧠 How It Works

1. **GitHub Webhook**: Set up a webhook on your repo to send commit data to our backend.
2. **Commit Parsing**: We extract relevant metadata from each push event (commit message, author, files changed, etc).
3. **Post Generation**: We summarize the changes using LLMs and generate a short social-ready post (X, LinkedIn).
4. **Manual or Auto-Share**: Choose to review, edit, or automatically post updates to your social channels.

## ✨ Features

- 📡 GitHub Webhook Integration
- 🧠 Commit Summarization using LLMs
- ✍️ Editable Post Templates
- 📅 Daily Digest or Real-Time Updates
- 👥 Multiple Developer Attribution
- 🔄 Optional cross-post to org Twitter/X or personal accounts

## 🔧 Setup

### 1. Clone the Repo

```bash
git clone https://github.com/your-org/source2social.git
cd source2social

