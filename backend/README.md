# Backend - CareerPilot Agent (FastAPI)

This is a minimal FastAPI backend with a health check and a file upload endpoint.

## Python setup (recommended: virtual environment)

1. Create and activate a virtual environment (macOS/Linux):
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

On Windows (PowerShell):
```powershell
cd backend
python -m venv .venv
.venv\\Scripts\\Activate.ps1
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server with auto-reload:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Endpoints

- GET `/health` → `{ "status": "ok" }`
- POST `/upload-resume` → accepts a multipart file under field name `file`, saves it under `backend/uploads/<uuid>.pdf`, and returns `{ ok: true, path: "..." }`

## How file uploads work

- The client sends a `multipart/form-data` request with a `file` field.
- FastAPI provides the file via `UploadFile`, which streams the content without loading it all into memory.
- The server writes the uploaded bytes into a file in the `uploads/` directory. We generate a UUID filename (with `.pdf`) to avoid collisions and to avoid trusting the client file name.
- For security, we do not execute or parse the file yet; we only save it. Any parsing (e.g., with `pdfplumber`) can happen later.

## CORS

CORS is enabled for `http://localhost:3000` to allow the Next.js frontend to call this API during local development.

## Logging

A simple structured logger is configured to print request logs and upload events to stdout.



