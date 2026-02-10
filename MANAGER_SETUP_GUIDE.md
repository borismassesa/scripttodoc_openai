# 🚀 ScriptToDoc - Manager Setup Guide

**Complete step-by-step instructions to run ScriptToDoc on your local machine**

No Azure subscription required! Just an OpenAI API key and 15 minutes of setup time.

---

## 📋 What You'll Need

Before starting, make sure you have:

1. **Git** - To clone the repository
2. **Python 3.9+** - To run the backend
3. **Node.js 18+** - To run the frontend
4. **OpenAI API Key** - Get one from [platform.openai.com](https://platform.openai.com/api-keys)

---

## ✅ Step 1: Check Prerequisites

Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux) and verify installations:

```bash
# Check Git
git --version
# Should show: git version 2.x.x

# Check Python
python3 --version
# Should show: Python 3.9.x or higher

# Check Node.js
node --version
# Should show: v18.x.x or higher

# Check npm
npm --version
# Should show: 9.x.x or higher
```

### If anything is missing:

- **Git**: Download from [git-scm.com](https://git-scm.com/downloads)
- **Python**: Download from [python.org](https://www.python.org/downloads/)
- **Node.js**: Download from [nodejs.org](https://nodejs.org/) (LTS version)

---

## 📥 Step 2: Clone the Repository

```bash
# Navigate to where you want to store the project (e.g., your Desktop)
cd ~/Desktop

# Clone the repository
git clone https://github.com/borismassesa/scripttodoc_openai.git

# Enter the project directory
cd scripttodoc_openai

# Verify files are there
ls
# You should see: backend/, frontend/, docs/, README.md, etc.
```

---

## 🔧 Step 3: Backend Setup

### 3.1 Navigate to Backend Directory

```bash
cd backend
```

### 3.2 Create Python Virtual Environment

**On Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` appear at the start of your command prompt.

### 3.3 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will take 2-3 minutes. You'll see many packages being installed.

### 3.4 Configure Environment Variables

```bash
# Copy the template to create your .env file
cp .env.template .env

# Now edit the .env file with your OpenAI API key
```

**On Mac:**
```bash
nano .env
# Or use: open -e .env (opens in TextEdit)
```

**On Windows:**
```cmd
notepad .env
```

**Replace this line:**
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

**With your actual OpenAI API key:**
```bash
OPENAI_API_KEY=sk-proj-ABC123YourActualKeyHere
```

**Save the file:**
- **Nano**: Press `Ctrl+O`, then `Enter`, then `Ctrl+X`
- **TextEdit/Notepad**: File → Save, then close

### 3.5 Create Data Directory

```bash
mkdir -p data/uploads data/documents
```

### 3.6 Test Backend

```bash
# Start the backend server
uvicorn api.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ Success!** The backend is running. Keep this terminal window open.

---

## 🎨 Step 4: Frontend Setup

Open a **NEW terminal window/tab** (keep the backend running in the first one).

### 4.1 Navigate to Frontend Directory

```bash
# Navigate back to project root first
cd ~/Desktop/scripttodoc_openai

# Then enter frontend directory
cd frontend
```

### 4.2 Install Node Dependencies

```bash
npm install
```

This will take 1-2 minutes. You'll see a progress bar.

### 4.3 Configure Frontend Environment

```bash
# Create .env.local file
touch .env.local

# Edit it
nano .env.local
# Or on Mac: open -e .env.local
# Or on Windows: notepad .env.local
```

**Add this line:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Save the file** (same as before).

### 4.4 Start Frontend

```bash
npm run dev
```

You should see:
```
  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
  - Environments: .env.local

 ✓ Ready in 2.3s
```

**✅ Success!** The frontend is running.

---

## 🎉 Step 5: Use the Application

1. **Open your web browser**
2. **Go to:** http://localhost:3000
3. **You should see the ScriptToDoc interface!**

### Test with Sample Transcript

Create a test file called `test_transcript.txt` with this content:

```
Meeting: How to Create a New User Account
Date: February 10, 2026

Presenter: Welcome everyone. Today I'll show you how to create a new user account in our system.

First, log into the admin dashboard using your admin credentials.

Next, click on the "Users" menu on the left sidebar.

Then, click the "Add New User" button in the top right corner.

Fill in the required fields: username, email, and password.

Finally, click "Create User" to save the new account.

That's it! The user will receive an email with their login credentials.

Any questions?
```

**Upload this file through the web interface:**
1. Click "Choose File" and select `test_transcript.txt`
2. Select your preferences (tone, audience)
3. Click "Generate Document"
4. Wait 6-8 seconds
5. Download your professional training document!

---

## 📊 What You Should See

### Backend Terminal:
```
INFO:     Processing job: <job-id>
INFO:     Local mode: Using OpenAI with model gpt-4o-mini
INFO:     Topic segmentation completed: 1 topics found
INFO:     Generated 6 steps from 1 chunks
INFO:     Document generated successfully
```

### Frontend Interface:
- Progress tracker showing: Preparing → Parsing → Segmenting → Generating → Formatting → Complete
- Real-time step counter: "Step 1 of 6", "Step 2 of 6", etc.
- Token usage and cost estimate
- Download buttons for DOCX, PDF, PPTX formats

---

## 🛠️ Troubleshooting

### Problem: "Module not found" error in backend

**Solution:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Problem: "OPENAI_API_KEY not set" error

**Solution:**
1. Check that `backend/.env` file exists
2. Open it and verify your API key is correct
3. Make sure there are no spaces around the `=` sign
4. Restart the backend server

### Problem: "Port 8000 already in use"

**Solution:**
```bash
# Find and kill the process using port 8000
# On Mac/Linux:
lsof -ti:8000 | xargs kill -9

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Then restart the backend
```

### Problem: Frontend can't connect to backend

**Solution:**
1. Verify backend is running on http://localhost:8000
2. Check `frontend/.env.local` has: `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. Restart the frontend server

### Problem: "npm install" fails

**Solution:**
```bash
# Clear npm cache and try again
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

---

## 🔄 Starting After First Setup

Once everything is set up, you only need to do this:

### Terminal 1 - Backend:
```bash
cd ~/Desktop/scripttodoc_openai/backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn api.main:app --reload --port 8000
```

### Terminal 2 - Frontend:
```bash
cd ~/Desktop/scripttodoc_openai/frontend
npm run dev
```

### Browser:
```
http://localhost:3000
```

---

## 💰 Cost Information

- **Model**: GPT-4o-mini (very cost-effective)
- **Average cost per document**: $0.15 - $0.30
- **Processing time**: 6-8 seconds for typical documents
- **Your OpenAI free tier**: $5 credit = ~25-30 documents

---

## 📚 Additional Resources

- **Full Documentation**: Check the `docs/` folder
- **Quick Start Guide**: See `QUICK_START.md` in project root
- **Architecture Details**: `docs/architecture/1_SYSTEM_ARCHITECTURE.md`
- **Troubleshooting**: `docs/guides/QUICKSTART.md`

---

## 🆘 Still Having Issues?

### Check the logs:

**Backend logs**: Look at the terminal where you ran `uvicorn`
**Frontend logs**: Look at the terminal where you ran `npm run dev`
**Browser console**: Press F12 in your browser, check the Console tab

### Common Issues:

1. **No Python 3.9+**: Upgrade Python
2. **No OpenAI API key**: Get one from platform.openai.com
3. **Firewall blocking ports**: Allow ports 3000 and 8000
4. **Old Node.js version**: Upgrade to Node.js 18+

---

## ✨ Features You Can Try

1. **Upload different file formats**: .txt, .docx, .pdf
2. **Customize output**: Change tone and target audience
3. **Add knowledge sources**: Paste URLs for additional context
4. **Control document length**: Set min/target/max steps
5. **Multiple formats**: Download as DOCX, PDF, or PPTX
6. **View processing details**: See token usage and cost

---

## 🎯 Quick Test Checklist

- [ ] Backend starts without errors
- [ ] Frontend opens at http://localhost:3000
- [ ] Can upload a text file
- [ ] Processing completes successfully
- [ ] Can download DOCX file
- [ ] Document opens in Microsoft Word
- [ ] Content looks professional and well-formatted

---

## 📞 Getting Help

If you encounter any issues:

1. Check the troubleshooting section above
2. Review the logs in both terminal windows
3. Verify all prerequisites are installed correctly
4. Make sure your OpenAI API key is valid and has credits

---

**Setup Time**: 10-15 minutes (first time)
**Subsequent Startups**: 1 minute
**Per-Document Cost**: $0.15-$0.30
**Processing Speed**: 6-8 seconds

**Congratulations! 🎉 You're now running ScriptToDoc locally!**
