ī# CivicAI Karnataka – Setup & Running Guide

This project consists of an AI-powered FastAPI backend and a Next.js frontend. To run this project, you need to set up and run both components.

## 1. Prerequisites
* **PostgreSQL**: Installed and running on your local machine.
* **Python**: Python 3.8+ installed.
* **Node.js**: Node.js (v18+) and `npm` installed.

---

## 2. Setup and Run the Backend

### Step A: Setup the Database
1. Open your PostgreSQL console or client (e.g., pgAdmin, psql, or DBeaver).
2. Create a new database named `civic_karnataka`:
   ```sql
   CREATE DATABASE civic_karnataka;
   ```
3. **Configure Database Connection**: The default credentials are set in [config.py](file:///c:/Users/Lenovo/Desktop/CIVIC/backend/app/core/config.py):
   ```
   postgresql://postgres:postgres@localhost:5432/civic_karnataka
   ```
   If your PostgreSQL username, password, host, or port are different, create a `.env` file in the root workspace directory and specify your `DATABASE_URL`:
   ```env
   DATABASE_URL=postgresql://<username>:<password>@<host>:<port>/civic_karnataka
   ```

### Step B: Install Dependencies & Run Database Seed
1. Open a terminal in the root workspace directory (`c:/Users/Lenovo/Desktop/CIVIC`).
2. Create and activate a Python virtual environment:
   * **Windows PowerShell**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * **Windows Command Prompt**:
     ```cmd
     python -m venv venv
     venv\Scripts\activate
     ```
   * **macOS/Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Install the required Python packages defined in [requirements.txt](file:///c:/Users/Lenovo/Desktop/CIVIC/backend/requirements.txt):
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Run the seed script in [seed.py](file:///c:/Users/Lenovo/Desktop/CIVIC/backend/app/seed.py) to create database tables and insert initial mock data (roles, departments, complaint categories, and test user accounts):
   ```bash
   python -m backend.app.seed
   ```

### Step C: Start the Backend Server
1. Start the FastAPI backend server using Uvicorn:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
2. The backend API will be available at **`http://127.0.0.1:8000`**.
3. You can access the interactive Swagger documentation at **`http://127.0.0.1:8000/docs`**.

---

## 3. Setup and Run the Frontend

1. Open a second terminal window.
2. Navigate into the `frontend` folder:
   ```bash
   cd frontend
   ```
3. Install the Node modules defined in [package.json](file:///c:/Users/Lenovo/Desktop/CIVIC/frontend/package.json):
   ```bash
   npm install
   ```
4. Start the Next.js development server:
   ```bash
   npm run dev
   ```
5. The frontend will be available in your browser at **`http://localhost:3000`**.

---

## 4. Default Accounts for Testing
Once both the backend and frontend are running, you can log in using these default credentials populated by [seed.py](file:///c:/Users/Lenovo/Desktop/CIVIC/backend/app/seed.py):

| Role | Email | Password |
| :--- | :--- | :--- |
| **Citizen** | `citizen@gmail.com` | `citizenpassword` |
| **BBMP Officer** | `officer.bbmp@civicai.gov.in` | `officerpassword` |
| **BWSSB Officer** | `officer.bwssb@civicai.gov.in` | `officerpassword` |
| **BESCOM Officer** | `officer.bescom@civicai.gov.in` | `officerpassword` |
| **Traffic Police Officer** | `officer.traffic@civicai.gov.in` | `officerpassword` |
| **Admin** | `admin@civicai.gov.in` | `adminpassword` |
