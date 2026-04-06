# 🐟 Tin Pact — Tinned Fish Tracker

A shared web app for tracking how many tins of fish your group eats collectively.

---

## Features
- Log tins eaten per day with your name
- Upload a photo of your tin
- Shared leaderboard
- Collective progress bar toward a target
- Auto-refreshes every 30 seconds for all viewers

---

## Run Locally

1. Make sure Python is installed (3.8+):
   ```
   python --version
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start the app:
   ```
   python app.py
   ```

4. Open your browser to: http://localhost:5000

---

## Deploy to the Internet (Free) — Railway

This is the easiest option. You'll get a public URL like `tin-pact.up.railway.app`.

### Steps:

1. **Create a free account** at https://railway.app

2. **Install the Railway CLI** (optional, or use their website):
   - Mac/Linux: `curl -fsSL https://railway.app/install.sh | sh`
   - Or just drag-and-drop the folder on their site

3. **Deploy via website:**
   - Go to https://railway.app/new
   - Click "Deploy from local directory"
   - Select this folder
   - Railway auto-detects Python and deploys it
   - You'll get a public URL in ~2 minutes

4. **Share the URL** with your group — everyone can access it instantly.

### Alternative: Render (also free)
1. Go to https://render.com
2. Create a new "Web Service"
3. Connect your GitHub repo (upload this folder to GitHub first)
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `gunicorn app:app`
6. Deploy!

---

## Notes
- Photos are stored in the `uploads/` folder on the server
- Data is stored in `data.json` — all entries persist
- The app auto-refreshes every 30 seconds so everyone stays in sync
