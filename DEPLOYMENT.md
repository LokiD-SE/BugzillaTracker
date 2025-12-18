# Cloud Deployment Guide

This guide covers various cloud hosting options for the Bugzilla Tracker.

## Option 1: GitHub Actions (Recommended - Free)

GitHub Actions can run your script on a schedule for free (with limits).

### Setup:

1. **The workflow file is already created** at `.github/workflows/bugzilla-tracker.yml`
2. **Add secrets to GitHub repository:**
   - Go to Settings → Secrets and variables → Actions
   - Add all your `.env` variables as secrets:
     - `BUGZILLA_API_KEY`
     - `GOOGLE_CHAT_WEBHOOK`
     - `BUGZILLA_URL`
     - `EMAIL`
     - `BUG_STATUS`
     - `CHECK_INTERVAL_MINUTES`

3. **Push to GitHub** - the workflow will run automatically

**Schedule:**
- **10 AM daily**: Fetches and posts initial bug list (from last 1 month)
- **Every hour**: Checks for status changes and notifies

**Pros:** Free, easy setup, no server management  
**Cons:** Limited to 2000 minutes/month on free tier, state file needs to be stored in repo

---

## Option 2: AWS Lambda + EventBridge

Run as a serverless function triggered on a schedule.

### Setup:

1. **Install AWS CLI and configure credentials**
2. **Create deployment package:**
   ```bash
   zip -r deployment.zip . -x "*.git*" "*.pyc" "__pycache__/*" "venv/*" ".env"
   ```
3. **Create Lambda function** (Python 3.12 runtime)
4. **Set environment variables** in Lambda configuration
5. **Create EventBridge rule** to trigger every 5 minutes
6. **Upload deployment package**

**Pros:** Pay per execution, highly scalable, managed service  
**Cons:** Requires AWS account, 15-minute max execution time

---

## Option 3: Google Cloud Functions + Cloud Scheduler

Similar to AWS Lambda but on Google Cloud.

### Setup:

1. **Install Google Cloud SDK**
2. **Deploy function:**
   ```bash
   gcloud functions deploy bugzilla-tracker \
     --runtime python312 \
     --trigger-http \
     --entry-point main \
     --set-env-vars BUGZILLA_API_KEY=xxx,GOOGLE_CHAT_WEBHOOK=xxx
   ```
3. **Create Cloud Scheduler job** to trigger the function

**Pros:** Free tier available, easy deployment  
**Cons:** Requires Google Cloud account

---

## Option 4: Heroku

Deploy as a web dyno that runs continuously.

### Setup:

1. **Create `Procfile`:**
   ```
   worker: python main.py
   ```
2. **Deploy:**
   ```bash
   heroku create bugzilla-tracker
   heroku config:set BUGZILLA_API_KEY=xxx GOOGLE_CHAT_WEBHOOK=xxx
   git push heroku main
   ```
3. **Scale worker:**
   ```bash
   heroku ps:scale worker=1
   ```

**Pros:** Easy deployment, free tier available  
**Cons:** Free tier discontinued, paid plans start at $7/month

---

## Option 5: DigitalOcean App Platform

Managed platform for running applications.

### Setup:

1. **Create `app.yaml`** (see below)
2. **Connect GitHub repository**
3. **Set environment variables** in App Platform dashboard
4. **Deploy**

**Pros:** Simple setup, managed infrastructure  
**Cons:** Paid service (~$5/month minimum)

---

## Option 6: VPS (DigitalOcean, Linode, AWS EC2)

Run on a virtual private server.

### Setup:

1. **Create a VPS** (Ubuntu 22.04 recommended)
2. **SSH into server:**
   ```bash
   git clone <your-repo>
   cd BugzillaTracker
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Create `.env` file** with your configuration
4. **Run as a service** using systemd (see `bugzilla-tracker.service` below)

**Pros:** Full control, persistent state, cost-effective  
**Cons:** Requires server management, ~$5-10/month

---

## Option 7: Railway

Modern platform for deploying applications.

### Setup:

1. **Connect GitHub repository**
2. **Set environment variables** in Railway dashboard
3. **Deploy automatically**

**Pros:** Very easy, free tier available  
**Cons:** Free tier has limits

---

## Recommended: GitHub Actions

For most users, GitHub Actions is the best option because:
- ✅ Free for public repositories
- ✅ No server management
- ✅ Easy to set up
- ✅ Automatic runs on schedule

See `.github/workflows/bugzilla-tracker.yml` for the configuration.

