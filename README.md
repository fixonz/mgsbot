# 🚀 Mogosu Telegram Bot

The easiest way to start your own bot. Just fork, deploy, and start mogging!

## ⚡ Deployment in 3 Minutes

### 1. Fork this Repository
Click the **Fork** button at the top right of this page to create your own copy.

### 2. Deploy to Render (Recommended)
Click the button below to deploy instantly:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=YOUR_GITHUB_REPO_URL)

*(Note: Replace `YOUR_GITHUB_REPO_URL` with your actual forked repo link!)*

### 3. Configure your Environment Variables
During deployment (or in the "Environment" tab later), set these:

| Variable | Description |
| :--- | :--- |
| `BOT_TOKEN` | Your Bot Token from [@BotFather](https://t.me/BotFather) |
| `ADMIN_IDS` | Your Telegram ID (get it from [@userinfobot](https://t.me/userinfobot)) |
| `TATUM_API_KEY` | Your Tatum.io API key for payment checking |
| `LTC_ADDRESSES` | 5 LTC addresses separated by commas (your own wallet) |
| `DB_PATH` | Set this to: `/data/bot_database.sqlite` (for persistence) |

---

## 🛠️ Management & Setup
Once the bot is running:
1. Send `/admin` to the bot (only you will have access).
2. Use the **Category** and **Item** menus to create your categories.
3. Add **Stock** (Secrets) via the admin panel.
4. Set up your bot's personality and images.

## 💾 Persistence (CRITICAL)
This bot uses **Volumes** to ensure your database doesn't reset when the server restarts. 
- On **Render**: The `render.yaml` file included handles this automatically by mounting a disk to `/data`.
- On **Railway**: You must manually add a **Volume** and mount it to the directory where your `.sqlite` file is stored.

---

*Powered by Mogosu Engine*
