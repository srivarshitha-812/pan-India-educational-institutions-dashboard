# Production Deployment Guide: Pan-India Educational Institutions Dashboard

This document provides complete instructions for deploying the **Pan-India Educational Institutions Executive Dashboard** to production environments.

---

## 1. System Architecture Overview

| Component | Technology / Detail | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (ES6+) | Instantaneous load, zero bundler overhead, works on all modern desktop and mobile browsers. |
| **Backend API** | Python 3.10+, FastAPI, Uvicorn / Gunicorn | Asynchronous high-throughput REST API serving KPI summaries, paginated records, Data Dictionary, and global search. |
| **Data Storage** | Tabular Excel/CSV + SQLite (`education_master.db`) | File-based official regulatory registers loaded into optimized in-memory search structures. |
| **Data Dictionary** | `DATA_DICTIONARY.xlsx` & `data/data_dictionary.json` | 97 documented fields across 11 sectors, distinguishing Source, Derived, and Calculated attributes. |
| **Port / Binding** | Configurable via `$PORT` and `$HOST` (Default: `8000`, `0.0.0.0`) | Automated container and cloud environment variable binding. |

---

## 2. Large Dataset Handling (UDISE+ 1.47M Schools)

> [!IMPORTANT]
> **No Browser Bloat Guarantee**: The complete UDISE+ census contains **1,466,682 records** (~640 MB). The dashboard architecture strictly avoids streaming large datasets directly into client browsers or holding redundant bulk tables in RAM:
> 1. **Executive Overview & Sources**: Uses precomputed metadata, column schemas, and geographical counts from `DataRegistry`.
> 2. **Individual List Pagination**: Final institute lists serve records via `/api/final/{list_id}/records` with server-side pagination (`page=1&page_size=50`), sorting, and filtering.
> 3. **Global Search**: High-performance inverted index across the 7,335 verified final institutions executes in sub-5 milliseconds.
> 4. **UDISE+ Deep Queries**: For individual school lookups, the platform references the SQLite master (`education_master.db`) or KYS track APIs.

---

## 3. Local Development Start

To run the application locally in development mode:

```bash
# 1. Ensure Python dependencies are installed
pip install -r requirements.txt

# 2. Run the dashboard server
python dashboard_server.py --port 8000 --host 127.0.0.1
```

Access the dashboard in your web browser:
👉 **`http://127.0.0.1:8000`**

---

## 4. Production Start Commands

### Option A: Direct Python / Uvicorn (Fastest)
```bash
python dashboard_server.py --port 8000 --host 0.0.0.0
```

### Option B: Production Gunicorn Multi-Worker (Recommended for Linux/Cloud)
```bash
gunicorn dashboard_server:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:${PORT:-8000} \
  --access-logfile - \
  --error-logfile -
```

---

## 5. Docker Deployment

### Single-Command Start with Docker Compose
```bash
# Build image and run in detached mode
docker compose up -d --build

# View container logs
docker compose logs -f

# Stop container
docker compose down
```

### Direct Docker CLI Build & Run
```bash
# Build production image
docker build -t pan-india-dashboard:latest .

# Run container with port mapping and read-only volume mounting
docker run -d \
  --name pan_india_dashboard \
  -p 8000:8000 \
  -e PORT=8000 \
  -e HOST=0.0.0.0 \
  -e ENV=production \
  -v "$(pwd)/Final Institute Lists:/app/Final Institute Lists:ro" \
  -v "$(pwd)/data:/app/data:ro" \
  pan-india-dashboard:latest
```

---

## 6. Cloud Platform Deployment

### Recommended Platform: Render / Railway / AWS App Runner / GCP Cloud Run

The repository includes a ready-to-use **`Procfile`**, **`Dockerfile`**, and **`requirements.txt`**.

#### Deploying on Render (Simplest Free/Low-Cost Cloud Option):
1. Create a new **Web Service** on [Render.com](https://render.com).
2. Connect your Git repository.
3. Configure the service:
   - **Environment**: `Python` (or `Docker`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn dashboard_server:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
4. Set Environment Variables in the Render dashboard:
   - `PORT`: `8000`
   - `ENV`: `production`
5. Click **Deploy Web Service**.
6. Render will assign a public URL (e.g., `https://pan-india-institutes.onrender.com`).

#### Deploying on Railway:
1. Click **New Project** → **Deploy from GitHub repo**.
2. Railway detects the `Procfile` and `requirements.txt` automatically.
3. Add a public domain under service **Settings** → **Networking**.

#### Deploying on Google Cloud Run:
```bash
# Build and deploy container directly to Cloud Run
gcloud run deploy pan-india-dashboard \
  --source . \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

---

## 7. Linux VPS Deployment (Ubuntu + Systemd + Nginx)

### Step 1: Systemd Service Configuration
Create `/etc/systemd/system/dashboard.service`:
```ini
[Unit]
Description=Pan-India Educational Institutions Dashboard
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/pan_india_dashboard
Environment="PATH=/var/www/pan_india_dashboard/venv/bin"
Environment="PORT=8000"
Environment="HOST=127.0.0.1"
Environment="ENV=production"
ExecStart=/var/www/pan_india_dashboard/venv/bin/gunicorn dashboard_server:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dashboard
sudo systemctl start dashboard
```

### Step 2: Nginx Reverse Proxy
Add to `/etc/nginx/sites-available/dashboard.conf`:
```nginx
server {
    listen 80;
    server_name dashboard.example.edu.in;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
    }

    # Static assets caching
    location /static/ {
        alias /var/www/pan_india_dashboard/static/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }
}
```

Enable site and configure SSL with Certbot:
```bash
sudo ln -s /etc/nginx/sites-available/dashboard.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d dashboard.example.edu.in
```

---

## 8. Security & Data Integrity

1. **No Hardcoded Secrets**: The application requires no database passwords or external API tokens.
2. **Read-Only Data Layer**: Source files and cleaned final lists are treated as strictly immutable by the web dashboard.
3. **Filesystem Path Sanitization**: All API endpoints return relative project paths (e.g. `data/processed/...`, `Final Institute Lists/...`) rather than internal host filesystem paths (`C:\Users\...`).
4. **Non-Root Execution**: Docker container runs under unprivileged `appuser` (UID 1001).
5. **Input Validation**: Search and query parameters are type-coerced and length-limited using FastAPI parameter validation.

---

## 9. Redeployment & Updating Data

When new datasets are collected or final lists are updated:

```bash
# 1. Pull latest code/data
git pull origin main

# 2. Re-generate Data Dictionary if schemas changed
python generate_data_dictionary.py

# 3. Restart the service
# On VPS:
sudo systemctl restart dashboard

# In Docker:
docker compose restart
```
