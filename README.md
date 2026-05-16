# AI-Powered-Smart-Study-Planner
AI-powered personalized study planner that analyzes uploaded materials, estimates syllabus difficulty, prioritizes topics, and generates adaptive schedules using RAG, embeddings, FastAPI, Next.js, PostgreSQL, ChromaDB, and Ollama.

## Email OTP setup

The backend uses SMTP to send the verification OTP.

### Option 1: Use Gmail with App Password
1. Enable 2FA for your Google account.
2. Create an App Password at https://support.google.com/accounts/answer/185833.
3. Set environment variables in `backend/.env` or your shell:

```powershell
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your@gmail.com
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
```

### Option 2: Local SMTP debugging without Docker
You can run Python's built-in SMTP debug server on Windows with:

```powershell
python -m smtpd -c DebuggingServer -n localhost:1025
```

Then use these env vars:

```powershell
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_NO_AUTH=true
EMAIL_FROM=no-reply@example.com
```

The OTP will be printed to the terminal running the debug SMTP server.

### Option 3: Console-only debug mode
If you want email behavior without a real SMTP server, set:

```powershell
SMTP_DEBUG=true
```

This makes the backend print OTP codes to the server console for development.
