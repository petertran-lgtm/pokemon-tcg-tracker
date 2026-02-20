# Deploy to Railway

Step-by-step guide to deploy the Pokemon TCG Tracker API.

## Prerequisites

- GitHub account
- Railway account (free at [railway.app](https://railway.app))

---

## Step 1: Create a new GitHub repo for the API

1. Go to [github.com/new](https://github.com/new)
2. **Repository name:** `pokemon-tcg-tracker` (or any name)
3. **Description (optional):** "Pokemon TCG market tracker API"
4. Choose **Public**
5. Do **not** check "Add a README" (we're pushing existing code)
6. Click **Create repository**
7. Leave this tab open — you'll need the repo URL

---

## Step 2: Push pokemon-tcg-tracker to the new repo

**Option A — If pokemon-tcg-tracker is a standalone folder:**

```bash
cd /Users/petertran/Documents/PM-OS/pokemon-tcg-tracker
git init
git add .
git commit -m "Initial commit: Pokemon TCG tracker API"
git remote add origin https://github.com/YOUR_USERNAME/pokemon-tcg-tracker.git
git branch -M main
git push -u origin main
```

**Option B — If you get "fatal: not a git repository" or the folder is inside another repo:**

1. Clone your new empty repo: `git clone https://github.com/YOUR_USERNAME/pokemon-tcg-tracker.git temp-deploy`
2. Copy all files from `pokemon-tcg-tracker` into `temp-deploy` (except `.venv`)
3. `cd temp-deploy && git add . && git commit -m "Initial commit" && git push`

---

## Step 3: Deploy on Railway

1. Go to [railway.app](https://railway.app)
2. Click **Login** and sign in with GitHub
3. Click **New Project**
4. Select **Deploy from GitHub repo**
5. Choose **Configure GitHub App** if prompted (authorize Railway)
6. Select your `pokemon-tcg-tracker` repo from the list
7. Click **Deploy**
8. Railway will detect Python, install dependencies, and start the app
9. Wait for the build to finish (1–2 minutes)

---

## Step 4: Get your public URL

1. In your Railway project, click on the **service** (the deployed app)
2. Open the **Settings** tab
3. Under **Networking**, click **Generate Domain**
4. Railway will assign a URL like `pokemon-tcg-tracker-production-xxxx.up.railway.app`
5. Copy this URL

---

## Step 5: Connect Lovable to the deployed API

1. Open your Lovable project (PokéMarket)
2. Find where the API base URL is set (e.g. in a config file or environment variable)
3. Change it from `http://localhost:8000` to your Railway URL, e.g.:
   ```
   https://pokemon-tcg-tracker-production-xxxx.up.railway.app
   ```
4. Redeploy or refresh your Lovable app
5. The app should now fetch data successfully

---

## Troubleshooting

- **Build fails:** Check the Railway logs. Ensure `requirements.txt` and `Procfile` are in the repo root
- **503/502 errors:** The app may still be starting. Wait 30 seconds and retry
- **Empty cards:** The seed runs on startup. If the DB is empty, the first request might return `[]`; refresh after a few seconds
