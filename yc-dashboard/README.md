# 🚀 YC Intelligence Platform

A production-grade data pipeline and full-stack analytics platform that tracks Y Combinator companies. This system automates the extraction of 1,000+ company profiles, monitors their growth history (snapshots), and provides a real-time dashboard for investors and analysts.

## 📋 Project Overview
Unlike simple scrapers, the **YC Intelligence Platform** is built for **data integrity** and **historical tracking**. It detects when a company changes its stage (e.g., from *Active* to *Public*) or employee count, preserving a timeline of these changes in the database.

### Key Features
* **🕷️ Advanced Scraper:** Uses **Playwright** (Headless Chromium) to handle dynamic infinite scrolling and heavy AJAX loads.
* **⏳ Time-Travel Data:** Implemented a "Snapshot" system. If a company updates its description or stage, the old data is kept, and a new snapshot is created.
* **🔍 Web Enrichment:** A secondary worker script visits company websites to detect **Careers Pages**, **Blogs**, and extract **Contact Emails**.
* **📊 Real-Time Analytics:** A Next.js dashboard featuring Recharts to visualize batch distribution, industry trends, and location hotspots.
* **🛡️ Robust Error Handling:** The scraper uses transactional rollback logic to ensure partial failures do not corrupt the database.
* **🔒 System Monitoring:** An internal Admin Dashboard tracks scraper performance, run times, and success rates.

---

## 🛠️ Tech Stack & Architecture

```mermaid
graph TD
    A[YC Website] -->|Playwright Scraper| B(Python Engine)
    B -->|Deduplication SHA256| C{PostgreSQL DB}
    D[Enrichment Worker] -->|Updates Emails| C
    E[Next.js API Layer] -->|SQL Queries| C
    F[React Frontend] -->|JSON Data| E

    yc-dashboard/
├── app/
│   ├── admin/              # System Status & Logs Page
│   ├── analytics/          # Global Analytics Charts
│   ├── api/                # Backend API Routes
│   │   ├── companies/      # CRUD for Company Data
│   │   └── runs/           # Scraper Log Endpoints
│   ├── companies/          # Dynamic Detail Pages ([id])
│   ├── page.tsx            # Main Dashboard (Search/Filter/Table)
│   └── layout.tsx          # Global UI Wrappers
├── public/                 # Static Assets
├── scraper_v6_production.py# Main Data Pipeline
├── enrichment_worker.py    # Email & Blog Detector
├── requirements.txt        # Python Dependencies
└── README.md               # Project Documentation

# Install Python dependencies
pip install playwright psycopg2 requests
playwright install chromium

# Run the Scraper
python scraper_v6_production.py

# (Optional) Run Enrichment
python enrichment_worker.py

# Install Node dependencies
npm install

# Start the Server
npm run dev

Open http://localhost:3000 to view the application.