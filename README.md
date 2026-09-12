# AIVOA Complaint Management System
> AI-powered Customer Complaint Management System for Pharmaceutical Manufacturing (API & FDF QA Module)

## Overview
**AIVOA Complaint Management System** is an enterprise-grade, full-stack Quality Assurance (QA) solution tailored for the pharmaceutical industry. The system streamlines, investigates, and automates customer complaint handling across both **Active Pharmaceutical Ingredients (API)** and **Finished Dosage Formulation (FDF)** manufacturing streams.

Using an agentic AI workflow orchestrated with **LangGraph** and powered by **Groq**, the system assists QA specialists in classifying complaints, evaluating product quality defects, performing root-cause analysis (RCA), and drafting Corrective and Preventive Actions (CAPA) in compliance with cGMP and global regulatory standards (e.g., FDA 21 CFR Part 211, EU GMP Annex 1).

---

## Architecture & Tech Stack

### Backend (`/backend`)
- **Runtime & Framework**: Python 3.12+, FastAPI
- **Agentic AI & LLMs**: LangGraph, LangChain-Groq
- **Database & ORM**: PostgreSQL, SQLAlchemy, psycopg2-binary
- **Validation & Serialization**: Pydantic v2
- **Server**: Uvicorn

### Frontend (`/frontend`)
- **Framework & Build**: React 18 / 19, Vite
- **State Management**: Redux Toolkit & React-Redux
- **Typography & Styling**: Google Inter Font, Modern Clean CSS Design Tokens
- **Icons**: Lucide React

---

## Project Structure

```
aivoa-complaint-system/
├── backend/
│   ├── .venv/                   # Python virtual environment
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py              # FastAPI application & health check
│   ├── .env.example             # Template environment variables
│   ├── .gitignore
│   └── requirements.txt         # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── store/               # Redux Toolkit store & slices
│   │   ├── App.jsx              # Main React landing view
│   │   ├── index.css            # Inter font styles & base tokens
│   │   └── main.jsx             # React entrypoint
│   ├── index.html               # HTML entry with Google Inter Font
│   ├── package.json             # Frontend dependencies & scripts
│   ├── vite.config.js           # Vite configuration
│   └── .gitignore
├── .gitignore                   # Root gitignore
└── README.md                    # Project documentation
```

---

## Getting Started

### 1. Backend Setup

1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Using uv (recommended)
   uv venv .venv --python 3.12
   .venv\Scripts\activate

   # Or using standard python
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and supply your GROQ_API_KEY and DATABASE_URL
   ```

5. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```
   - Health Check: [http://localhost:8001/health](http://localhost:8001/health)
   - Interactive Docs (Swagger): [http://localhost:8001/docs](http://localhost:8001/docs)

---

### 2. Frontend Setup

1. Open a terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
   - Access the application at [http://localhost:5173](http://localhost:5173)

---

## Module Scope (API & FDF QA)
- **Active Pharmaceutical Ingredients (API)**:
  - Chemical impurities, assay deviations, physical characteristics (color, particle size distribution), packaging integrity.
- **Finished Dosage Formulation (FDF)**:
  - Dissolution/disintegration failures, content uniformity, physical defects (chipping, capping, leakage), labeling and secondary packaging anomalies.
