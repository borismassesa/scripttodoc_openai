# ScriptToDoc - Quick Reference Card

**For Daily Use After Initial Setup**

---

## 🚀 Starting the Application (2 Steps)

### Terminal 1 - Backend
```bash
cd ~/Desktop/scripttodoc_openai/backend
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

### Terminal 2 - Frontend
```bash
cd ~/Desktop/scripttodoc_openai/frontend
npm run dev
```

### Browser
```
http://localhost:3000
```

---

## 🛑 Stopping the Application

- Press `Ctrl+C` in both terminal windows
- Type `deactivate` to exit Python virtual environment (optional)

---

## 📝 Usage Flow

1. **Upload** → Choose transcript file (.txt, .docx, .pdf)
2. **Configure** → Select tone, audience, and document structure
3. **Add URLs** → (Optional) Paste knowledge source URLs
4. **Generate** → Click button and wait 6-8 seconds
5. **Download** → Get DOCX, PDF, or PPTX format

---

## 💡 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | Run: `lsof -ti:8000 \| xargs kill -9` |
| Backend won't start | Check `.env` has valid `OPENAI_API_KEY` |
| Frontend error | Verify backend is running first |
| Upload fails | Check file is < 5MB |
| No document generated | Check OpenAI API credits |

---

## 📊 Performance Metrics

- **Processing Time**: 6-8 seconds
- **Cost per Document**: $0.15-$0.30
- **Average Output**: 8-12 steps
- **Supported Formats**: TXT, DOCX, PDF → DOCX, PDF, PPTX

---

## 🔗 Important URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **GitHub Repo**: https://github.com/borismassesa/scripttodoc_openai

---

## 📞 Need Help?

1. Check terminal logs for errors
2. See full guide: `MANAGER_SETUP_GUIDE.md`
3. Review documentation in `docs/` folder
4. Check browser console (F12)

---

**Remember**: Keep both terminal windows open while using the application!
