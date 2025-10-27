# 🚀 NeuralStark - Quick Start Guide

## One-Command Setup & Launch for Clean Linux

### Step 1: Run the Setup Script

From the `/app` directory, run:

```bash
chmod +x run.sh
./run.sh
```

This script will automatically:
- ✅ **Detect your Linux distribution** (Ubuntu, Debian, CentOS, RHEL, Fedora)
- ✅ **Install system dependencies** (Python, Node.js, MongoDB, Supervisor)
- ✅ **Install OCR tools** (Tesseract OCR, Poppler-utils)
- ✅ **Set up Python virtual environment**
- ✅ **Install Python backend dependencies**
- ✅ **Install frontend dependencies** (with Yarn)
- ✅ **Configure MongoDB** and start service
- ✅ **Create necessary directories and sample documents**
- ✅ **Configure and start all services** (Backend, Frontend)
- ✅ **Verify everything is running**

**Time required:** ~5-10 minutes on clean system (depending on internet speed)

**Works on:**
- Ubuntu 18.04+ / Debian 10+
- CentOS 7+ / RHEL 7+ / Fedora 30+
- Pop!_OS, Linux Mint, and other Debian/Ubuntu derivatives

### Step 2: Configure Your API Key

1. Open the application in your browser (check your deployment URL)
2. Navigate to **Settings** page
3. Enter your **Gemini API key**
   - Get it from: https://aistudio.google.com/app/apikey
4. Click **Save**

### Step 3: Add Documents

Add your documents to the `/app/files` directory:

```bash
# Example: Copy documents
cp /path/to/your/document.pdf /app/files/

# Or create a new document
nano /app/files/my-notes.txt
```

**Supported formats:**
- PDF (with OCR), Word (.doc, .docx), Excel (.xls, .xlsx)
- OpenDocument (.odt), Text (.txt), Markdown (.md)
- JSON (.json), CSV (.csv)

### Step 4: Start Chatting!

1. Go to the **Chat** page
2. Wait a few seconds for document indexing
3. Ask questions about your documents!

**Example questions:**
- "What is this document about?"
- "Summarize the main points"
- "What are the key findings?"
- "Quels sont les points importants?" (French)

---

## 🔧 Troubleshooting

### Services Not Starting

Check service status:
```bash
sudo supervisorctl status
```

Restart services:
```bash
sudo supervisorctl restart all
```

### View Logs

Backend logs:
```bash
tail -f /var/log/supervisor/backend.err.log
```

Frontend logs:
```bash
tail -f /var/log/supervisor/frontend.out.log
```

### Documents Not Indexing

Manually trigger reindexing:
1. Go to Settings page
2. Click "🔄 Reindex Documents" button

Or via API:
```bash
curl -X POST http://localhost:8001/api/documents/reindex
```

### Chat Not Working

1. ✅ Verify Gemini API key is configured in Settings
2. ✅ Check that documents are indexed (Settings page shows count > 0)
3. ✅ Check backend logs for errors

---

## 📊 Monitoring

### Check Document Status

Via UI: Go to Settings page

Via API:
```bash
curl http://localhost:8001/api/documents/status
```

### Check Backend Health

```bash
curl http://localhost:8001/api/
```

Expected response:
```json
{
  "message": "NeuralStark API",
  "status": "running"
}
```

---

## 🎯 Tips for Best Results

### Document Quality
- Use clear, well-formatted documents
- Avoid heavily scanned/low-quality PDFs
- Text-based PDFs work better than image-only PDFs

### Query Tips
- Be specific in your questions
- Reference document names if you have many files
- Try different phrasings if you don't get good results

### Performance
- First query may be slower (embedding model loading)
- Subsequent queries are faster
- Large documents take longer to index

---

## 🔄 Re-running the Setup

If you need to reinstall or reset:

```bash
# Stop services
sudo supervisorctl stop all

# Run setup again
./run.sh

# Services will restart automatically
```

---

## 📚 Additional Resources

- **Full Documentation:** See `/app/README.md`
- **API Documentation:** Included in README.md
- **Architecture Details:** See README.md

---

## 🆘 Need Help?

1. Check the logs (commands above)
2. Review `/app/README.md` for detailed documentation
3. Verify all dependencies are installed
4. Ensure MongoDB is running: `sudo supervisorctl status mongodb`

---

**🎉 You're all set! Enjoy chatting with your documents!**
