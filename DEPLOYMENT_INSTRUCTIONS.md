# VivaBot Deployment Instructions - FREE TIER

**Your GitHub repo is ready for deployment!**

## 🎯 Quick Start (Follow these steps in order)

### STEP 1: Set Up Supabase Database (15 min)

1. **Go to https://supabase.com**
2. Click **"Start your project"**
3. Sign up with GitHub (use your account: vishsakshi)
4. Create new project:
   - **Project name**: vivabot
   - **Database password**: Create a strong password (save it!)
   - **Region**: Choose closest to you (e.g., us-east-1)
5. Wait 2-3 minutes for project to be ready
6. Go to **Settings → Database → Connection String**
7. Copy the connection string (it looks like: `postgresql://user:password@host:5432/postgres`)
8. **Save this string - you'll need it for Render**

### STEP 2: Create Database Tables in Supabase

1. In Supabase dashboard, go to **SQL Editor**
2. Click **"New Query"**
3. Copy and run this SQL to create tables:

```sql
-- Enable vector extension for RAG
CREATE EXTENSION IF NOT EXISTS vector;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vivas Table
CREATE TABLE IF NOT EXISTS vivas (
    viva_id VARCHAR(100) PRIMARY KEY,
    faculty_id BIGINT REFERENCES users(id),
    subject VARCHAR(255),
    course_code VARCHAR(50),
    topic VARCHAR(255),
    question_count INTEGER,
    duration_minutes INTEGER,
    batch_name VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Questions Table
CREATE TABLE IF NOT EXISTS questions (
    question_id VARCHAR(100) PRIMARY KEY,
    viva_id VARCHAR(100) REFERENCES vivas(viva_id),
    question_text TEXT,
    ideal_answer TEXT,
    subject VARCHAR(255),
    topic VARCHAR(255),
    evaluation_rubric JSONB,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evaluations Table
CREATE TABLE IF NOT EXISTS evaluations (
    evaluation_id VARCHAR(100) PRIMARY KEY,
    question_id VARCHAR(100) REFERENCES questions(question_id),
    student_id VARCHAR(100),
    student_answer TEXT,
    status VARCHAR(50),
    ai_score FLOAT,
    faculty_score FLOAT,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Embeddings Table for RAG/Vector Search
CREATE TABLE IF NOT EXISTS embeddings (
    id BIGSERIAL PRIMARY KEY,
    document_id VARCHAR(255),
    content TEXT,
    embedding vector(1536),
    viva_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

4. Click **"Run"** to execute

### STEP 3: Deploy Backend on Render (20 min)

1. **Go to https://render.com**
2. Click **"Sign up with GitHub"**
3. Click **"Import Project"**
4. Select your **AutoViva** repository
5. Click **"Continue"**
6. Fill in deployment details:
   - **Project name**: vivabot-backend
   - **Environment**: Python 3
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. Click **"Create Web Service"** (wait 3-5 minutes for deployment)

**After deployment, go to Environment Variables:**
1. Click on your service
2. Go to **Environment** section
3. Add these variables:

```
DATABASE_URL = postgresql://user:password@host:5432/postgres
OPENAI_API_KEY = your_openai_api_key
QWEN_API_KEY = your_qwen_api_key
JWT_SECRET = generate_random_secret
SECRET_KEY = generate_random_secret
ENVIRONMENT = production
```

**To generate secrets:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

4. Click **"Save"** (backend restarts automatically)
5. **Copy your backend URL**: `https://vivabot-backend.onrender.com`

### STEP 4: Deploy Frontend on Vercel (15 min)

1. **Go to https://vercel.com**
2. Click **"Sign up with GitHub"**
3. Click **"Add New..."** → **"Project"**
4. Select your **AutoViva** repository
5. Click **"Import"**
6. Configure project:
   - **Project name**: vivabot
   - **Framework Preset**: Vite
   - **Root Directory**: ./frontend
   - **Build command**: npm run build
   - **Output directory**: dist
7. Click **"Deploy"** (wait 2-3 minutes)

**After deployment, add Environment Variable:**
1. Go to **Settings** → **Environment Variables**
2. Add:
   ```
   VITE_API_URL = https://vivabot-backend.onrender.com
   ```
3. Redeploy to apply changes
4. **Copy your frontend URL**: `https://vivabot.vercel.app`

### STEP 5: Test Deployment (10 min)

1. **Open frontend URL in browser**: https://vivabot.vercel.app
2. Check if page loads (may take 10-30 seconds first time)
3. Test login functionality
4. If backend is slow (first request), wait 10 seconds
5. All features should work as before!

---

## 🎯 Your Live URLs

After deployment:
```
Frontend:  https://vivabot.vercel.app
Backend:   https://vivabot-backend.onrender.com
Database:  Supabase (admin dashboard: https://app.supabase.com)
```

---

## ⚠️ Important Notes

### Render Auto-Sleep (Free Tier)
- Backend sleeps after 15 minutes of inactivity
- First request wakes it up (5-10 second delay)
- **Solution**: Set up UptimeRobot (see below)

### Auto-Deploy on Code Push
- Push code to GitHub `main` branch
- Vercel automatically redeploys frontend
- Render automatically redeploys backend
- **No manual deployment needed!**

---

## 🔧 Set Up UptimeRobot (Optional but Recommended - 5 min)

**To prevent Render from sleeping:**

1. Go to https://uptimerobot.com
2. Sign up for free account
3. Click **"Add New Monitor"**
4. Fill in:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: VivaBot Backend
   - **URL**: https://vivabot-backend.onrender.com/health
   - **Monitoring Interval**: 5 minutes
5. Click **"Create Monitor"**
6. Backend will never sleep now! ✅

---

## 🆘 Troubleshooting

### "CORS Error" or "API not responding"
- Wait 10 seconds (first request wakes up backend)
- Check Render logs: Render dashboard → Select service → Logs
- Verify DATABASE_URL is correct in Render environment variables

### "Frontend won't load"
- Hard refresh browser: Ctrl+Shift+Delete (clear cache)
- Check browser console (F12) for errors
- Verify VITE_API_URL in Vercel environment variables

### "Database connection refused"
- Check DATABASE_URL in Render environment variables
- Verify password doesn't have special characters
- In Supabase, check if IP allowlist allows connections

### "Questions won't generate"
- Check OPENAI_API_KEY and QWEN_API_KEY are correct
- Verify they have credits/balance remaining
- Check backend logs in Render

---

## 📊 Monitoring & Logs

### View Backend Logs
```
Render Dashboard → Select vivabot-backend → Logs tab
```

### View Frontend Logs
```
Vercel Dashboard → vivabot → Deployments → View Function Logs
```

### View Database Logs
```
Supabase Dashboard → Logs (realtime, SQL queries)
```

---

## ✅ All Done!

Your VivaBot is now **LIVE and FREE** on:
- **Frontend**: https://vivabot.vercel.app
- **Backend**: https://vivabot-backend.onrender.com

**Cost: $0/month** ✅

No code changes needed - everything works exactly the same!

---

## 📝 Quick Reference

| Component | Service | Status | URL |
|-----------|---------|--------|-----|
| Frontend | Vercel | Auto-Deploy | https://vivabot.vercel.app |
| Backend | Render | Auto-Deploy | https://vivabot-backend.onrender.com |
| Database | Supabase | Free 500MB | https://app.supabase.com |
| Monitoring | UptimeRobot | Optional | https://uptimerobot.com |

---

**Questions? Check the logs in each service dashboard!**
