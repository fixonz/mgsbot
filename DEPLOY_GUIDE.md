# Deployment Guide for Railway

To run your bot automatically 24/7 on Railway, follow these steps:

## 1. Prepare your GitHub Repository
1. Initialize a git repository if you haven't:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Railway"
   ```
2. Create a new repository on GitHub and push your code there.
   *Note: My `.gitignore` will prevent your `.env` and `.sqlite` files from being uploaded, which is necessary for security.*

## 2. Deploy to Railway
1. Go to [Railway.app](https://railway.app/) and log in.
2. Click **+ New Project** -> **Deploy from GitHub repo**.
3. Select your repository.
4. Click **Add Variables** and copy the values from your local `.env` file:
   - `BOT_TOKEN`
   - `ADMIN_IDS`
   - `TATUM_API_KEY`
   - `LTC_ADDRESSES`

## 3. Important: Data Persistence (SQLite)
Railway uses an ephemeral file system by default. This means your database (`bot_database.sqlite`) will be **reset** every time the bot restarts or you push an update.

**To fix this:**
1. In Railway, go to your project settings.
2. Click **Add Service** -> **Volume**.
3. Mount the volume to `/app/data` (or similar).
4. Update `database.py` to point to the volume path.

*Alternatively, consider moving to a managed PostgreSQL database on Railway for better reliability.*

## 4. Why did the bot crash earlier?
The error `terminated by other getUpdates request` means you had **two copies** of the bot running at the same time with the same token. Telegram only allows one at a time. Before starting the bot on Railway, make sure you close the one running on your computer.
