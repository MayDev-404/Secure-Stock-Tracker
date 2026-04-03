# Secure Stock Tracker

A full-stack application for securely tracking stock prices in real-time. It consists of a Python FastAPI backend and a React (Vite) frontend. The application emphasizes security by utilizing HTTPS, WSS (Secure WebSockets), and JWT-based authentication.

## Project Structure
- **/backend** - FastAPI server providing REST endpoints and WebSocket connections.
- **/frontend** - React single-page application built with Vite.

## Backend Setup (FastAPI)

The backend requires Python 3.8+ and uses `aiosqlite` for asynchronous database operations.

### 1. Create a Virtual Environment
It's highly recommended to use a virtual environment to manage dependencies:
```bash
# Navigate to the backend directory
cd backend

# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate TLS Certificates (for local HTTPS)
The application requires TLS certificates to run securely. Run the provided script to generate self-signed certificates (`cert.pem` and `key.pem`):
```bash
python generate_cert.py
```

### 4. Run the Backend Server
Start the FastAPI server with `uvicorn`, specifying the SSL certificates:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

The server will start on `https://localhost:8000`, and its automatic API documentation will be available at `https://localhost:8000/docs`.



## Frontend Setup (React/Vite)

The frontend requires Node.js (v18+ recommended) and uses `@vitejs/plugin-basic-ssl` to serve the app over HTTPS locally.

### 1. Install Dependencies
```bash
# Navigate to the frontend directory
cd frontend

# Install packages
npm install
```

### 2. Run the Development Server
```bash
npm run dev -- --host
```

Vite will start the development server on `https://localhost:5173`. 


## Important Notes on Self-Signed Certificates
Since the local development servers use self-signed certificates, your browser will likely show a "Your connection is not private" or security warning when you first access the application. 
- You must click **"Advanced"** and then **"Proceed to localhost (unsafe)"** to view the app. 
- You may also need to do this for the backend API by navigating to `https://localhost:8000/docs` in a separate tab and accepting the certificate warning, so that the frontend's API requests aren't blocked by the browser.
