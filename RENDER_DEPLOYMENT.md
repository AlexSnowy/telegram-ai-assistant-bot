# 🚀 Deployment to Render - Complete Guide

## ✅ Why Render?
- **750 free hours/month** (more than Railway's 500)
- **No auto-stop** on free tier (unlike Railway)
- **Fast deployment** from GitHub
- **Simple setup**

## 📋 Pre-flight Checklist

- [x] Code pushed to GitHub: `https://github.com/AlexSnowy/telegram-ai-assistant-bot`
- [x] `render.yaml` configured
- [x] All required files present
- [x] Environment variables ready

## 🔧 Required Environment Variables

You need to add these **as Render Secrets** (Dashboard → Environment → Secrets):

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here (optional)
OPENAI_API_KEY=your_openai_api_key_here (optional)
FIRESTORE_PROJECT_ID=your_firestore_project_id (optional)
FIREBASE_CREDENTIALS=your_firebase_json_key (optional)
```

**Note:** Render uses **Secrets** for sensitive data (recommended) or you can use plain Environment Variables.

## 🎯 Step-by-Step Deployment

### 1. Create Render Account
1. Go to https://render.com
2. Sign up / Log in (GitHub integration recommended)

### 2. Create New Web Service
1. Click **"New +"** (top right) → **"Web Service"**
2. Connect your GitHub repository:
   - Select `telegram-ai-assistant-bot`
   - Click **"Connect"**

### 3. Configure Service
Render will auto-detect `render.yaml` and fill settings:

- **Name**: `telegram-ai-assistant` (or your preferred name)
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt` (auto-filled)
- **Start Command**: `python app.py` (auto-filled)
- **Plan**: **Free** (important!)
- **Health Check Path**: `/` (auto-filled from render.yaml)
- **Auto-Deploy**: Enable (auto-filled)

### 4. Add Environment Variables / Secrets

**Option A: Using Secrets (Recommended)**
1. In your service dashboard, go to **"Environment"** tab
2. Scroll to **"Secrets"** section
3. Click **"Add Secret"** for each:
   - `TELEGRAM_BOT_TOKEN` → your bot token
   - `GOOGLE_API_KEY` → your Gemini API key
   - `GROQ_API_KEY` → your Groq key (optional)
   - `OPENAI_API_KEY` → your OpenAI key (optional)
   - `FIRESTORE_PROJECT_ID` → your Firebase project ID (optional)
   - `FIREBASE_CREDENTIALS` → paste entire JSON key (optional)

**Option B: Using Environment Variables**
Same steps but in "Environment Variables" section (not encrypted).

### 5. Create Service
- Click **"Create Web Service"**
- Wait for build (2-5 minutes)
- Render will automatically deploy on GitHub push

### 6. Get Your URL
After successful deployment:
- Go to your service **"Dashboard"**
- Copy the URL (e.g., `https://telegram-ai-assistant.onrender.com`)

### 7. Set Telegram Webhook
Open terminal and run:

```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=YOUR_RENDER_URL/webhook"
```

**Example:**
```bash
curl -X POST "https://api.telegram.org/bot8763371380:AAE3iA-rOEWrYzKtAYFB55XiUN5nlGZAoZo/setWebhook?url=https://telegram-ai-assistant.onrender.com/webhook"
```

### 8. Verify
1. Check webhook status:
```bash
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"
```
2. Send message to your bot in Telegram
3. Check Render logs: Dashboard → **Logs**

## 📊 Render vs Railway Comparison

| Feature | Render | Railway |
|---------|--------|---------|
| **Free hours** | 750/month | 500/month |
| **Auto-stop** | ❌ No | ✅ Yes (after 15 min inactivity) |
| **Cold start** | ~10-15 sec | ~5-10 sec |
| **Health checks** | ✅ Built-in | ✅ Configurable |
| **Auto-deploy** | ✅ Yes | ✅ Yes |
| **Secrets management** | ✅ Secrets | ✅ Variables |
| **Ease of use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Verdict:** Render is better for production due to no auto-stop!

## 🐛 Troubleshooting

### Build Fails
- Check `requirements.txt` is valid
- Ensure Python version compatibility (3.8+)
- Review build logs in Render

### Bot Not Responding
1. Verify all environment variables/secrets are set
2. Check logs for errors
3. Confirm webhook is set correctly
4. Test AI API keys are valid

### Webhook Errors
- Bot token must be correct
- URL must be HTTPS
- Bot must be running before setting webhook

### Service Sleeps After Inactivity
- **Render free tier does NOT auto-stop** (unlike Railway)
- If service sleeps, first request will be slow (cold start ~10-15 sec)
- This is normal for free hosting

## 📈 Monitoring

- **Logs**: Render Dashboard → Logs (real-time)
- **Metrics**: Render Dashboard → Metrics
- **Events**: Render Dashboard → Events
- **Console**: View full logs with timestamps

## 🔄 Updates

- **Automatic**: Push to GitHub → Render auto-deploys
- **Manual**: Dashboard → "Manual Deploy"

## ⚠️ Important Notes

1. **Free Tier Limits**: 750 hours/month (enough for 24/7)
2. **Instance Sleep**: Render free tier does NOT stop automatically
3. **Database**: Local `users_local.json` won't persist across instances - use Firebase Firestore for production
4. **Files**: All knowledge base files are included in deployment

## 📚 Additional Resources

- Full deployment guide: `DEPLOY.md`
- Railway deployment: `RAILWAY_DEPLOYMENT.md`
- Setup webhook script: `setup_webhook.py`

---

**Status:** Ready to deploy. All configuration files are in place and code is on GitHub.

**Next Action:** Create Render Web Service and add environment variables/secrets.
