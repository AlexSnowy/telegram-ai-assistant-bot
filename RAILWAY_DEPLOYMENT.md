# 🚀 Deployment to Railway - Complete Guide

## ✅ Pre-flight Checklist

- [x] Code pushed to GitHub: https://github.com/AlexSnowy/telegram-ai-assistant-bot/tree/main
- [x] Repository is public/accessible
- [x] All configuration files present:
  - railway.json
  - Procfile
  - requirements.txt
  - app.py (entry point)
- [x] Environment variables collected

## 📦 Required Environment Variables

Add these to your Railway project **Variables** section:

```
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
FIRESTORE_PROJECT_ID=YOUR_FIRESTORE_PROJECT_ID_HERE
```

**Note:** Replace the placeholder values with your actual API keys and project ID.

**Optional (if using Firebase):**
```
FIREBASE_CREDENTIALS=<service-account-json-content>
```

## 🎯 Step-by-Step Deployment

### 1. Create Railway Project

1. Go to https://railway.app
2. Sign in with GitHub
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose repository: `telegram-ai-assistant-bot`
6. Railway will auto-detect `railway.json` and start building

### 2. Configure Variables

After project creation:

1. Go to your project dashboard
2. Click **"Variables"** in the left sidebar
3. Click **"Add Variable"**
4. Add each variable from the list above
5. Click **"Save"**

### 3. Trigger Deploy

- Railway auto-deploys on GitHub push (already done)
- Or manually: **"Deployments"** → **"New Deploy"**
- Wait for build (2-5 minutes)

### 4. Get Service URL

After successful deployment:

1. Go to **"Settings"** tab
2. Under **"Domains"** section
3. Copy your URL (should be `*.up.railway.app`)
4. Example: `https://worker-production-b2d5.up.railway.app`

### 5. Set Telegram Webhook

Open terminal and run:

```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=YOUR_RAILWAY_URL"
```

Replace `YOUR_BOT_TOKEN` with your actual bot token and `YOUR_RAILWAY_URL` with your actual Railway URL.

**Example:**
```bash
curl -X POST "https://api.telegram.org/bot8763371380:AAE3iA-rOEWrYzKtAYFB55XiUN5nlGZAoZo/setWebhook?url=https://worker-production-b2d5.up.railway.app"
```

### 6. Verify Deployment

**Check webhook status:**
```bash
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"
```

Expected output:
```json
{
  "ok": true,
  "result": {
    "url": "https://worker-production-b2d5.up.railway.app",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "last_error_date": null,
    "last_error_message": null
  }
}
```

**Test the bot:**
1. Open Telegram
2. Send `/start` to your bot
3. Check Railway logs: Dashboard → **"Logs"** tab

## 🔧 Configuration Details

### railway.json
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python app.py",
    "healthcheckPath": "/",
    "healthcheckTimeout": 300,
    "restartPolicy": {
      "type": "ON_FAILURE",
      "maxAttempts": 3
    }
  }
}
```

### Procfile
```
web: python app.py
```

### Entry Point
- `app.py` - Flask web server with `/` (health) and `/webhook` (Telegram) endpoints

## 🐛 Troubleshooting

### Build Fails
- Check `requirements.txt` exists and is valid
- Ensure Python version is compatible (3.8+)
- Review build logs in Railway

### Bot Not Responding
1. Verify all environment variables are set
2. Check logs for errors
3. Confirm webhook is set correctly
4. Test AI API keys are valid

### Webhook Errors
- Ensure bot token is correct
- URL must be HTTPS
- Bot must be running before setting webhook

### Cold Start Delays
- Free tier may sleep after inactivity
- First request after sleep will be slow (5-15 seconds)
- This is normal for free hosting

## 📊 Monitoring

- **Logs**: Railway Dashboard → Logs
- **Metrics**: Railway Dashboard → Metrics
- **Domains**: Settings → Domains
- **Variables**: Variables tab

## 🔄 Updates

- Automatic: Push to GitHub → Railway auto-deploys
- Manual: Deployments → New Deploy

## 📚 Additional Resources

- Full deployment guide: `DEPLOY.md`
- Quick start: `QUICK_DEPLOY.md`
- Setup webhook script: `setup_webhook.py`

---

**Status:** Ready to deploy. All configuration files are in place and code is on GitHub.

**Next Action:** Create Railway project and add environment variables.
