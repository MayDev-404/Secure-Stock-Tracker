import asyncio
import logging
import random
import json
import time
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import init_db, update_stock_price, get_all_stocks, get_stock_by_symbol, add_new_stock, create_user, get_user_by_username, log_session_event
from tcp_layer import start_custom_tcp_server, tcp_manager

# Security configs
SECRET_KEY = "super-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IPRateLimiter:
    def __init__(self, max_requests=20, window_seconds=5.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = {}

    def is_allowed(self, ip: str) -> bool:
        current_time = time.time()
        if ip not in self.clients:
            self.clients[ip] = []
        
        # Filter strictly within window tracking requests per unique IP natively
        self.clients[ip] = [t for t in self.clients[ip] if current_time - t < self.window_seconds]
        
        if len(self.clients[ip]) >= self.max_requests:
            return False
        
        self.clients[ip].append(current_time)
        return True

rate_limiter = IPRateLimiter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[websocket] = username
        logger.info(f"Client connected: {username}. Total clients: {len(self.active_connections)}")
        asyncio.create_task(log_session_event(username, "connect"))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            username = self.active_connections.pop(websocket)
            logger.info(f"Client disconnected: {username}. Total clients: {len(self.active_connections)}")
            asyncio.create_task(log_session_event(username, "disconnect"))

    async def broadcast(self, message: str):
        if not self.active_connections:
            return
            
        start_time = time.perf_counter()
        
        tasks = [connection.send_text(message) for connection in list(self.active_connections.keys())]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for conn, result in zip(list(self.active_connections.keys()), results):
            if isinstance(result, Exception):
                self.disconnect(conn)
                
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(f"PERFORMANCE: Server seamlessly broadcasted identical payload resolving across {len(tasks)} parallel clients directly routing within exactly {elapsed:.3f}ms overhead")

manager = ConnectionManager()

# Background task for simulating stocks
async def simulate_stock_prices():
    logger.info("Starting stock price simulation...")
    while True:
        try:
            stocks = await get_all_stocks()
            if not stocks:
                await asyncio.sleep(2)
                continue
                
            stock = random.choice(stocks)
            symbol = stock['symbol']
            current_price = stock['price']
            
            change_percent = random.uniform(-0.02, 0.02)
            new_price = round(current_price * (1 + change_percent), 2)
            
            await update_stock_price(symbol, new_price)
            
            if manager.active_connections or getattr(tcp_manager, 'active_connections', None):
                update_msg = json.dumps({
                    "type": "MKT_UPDATE",
                    "data": {"symbol": symbol, "price": new_price}
                })
                
                dispatch_tasks = []
                if manager.active_connections:
                    dispatch_tasks.append(manager.broadcast(update_msg))
                if getattr(tcp_manager, 'active_connections', None):
                    dispatch_tasks.append(tcp_manager.broadcast(update_msg))
                    
                if dispatch_tasks:
                   await asyncio.gather(*dispatch_tasks)
                
            # Expose backend simulation explicitly dropping delays directly multiplying output streams aggressively
            await asyncio.sleep(random.uniform(0.05, 0.2))
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in simulation loop: {e}")
            await asyncio.sleep(1)

background_task = None

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing asynchronous database...")
    await init_db()
    
    asyncio.create_task(start_custom_tcp_server())
    
    global background_task
    background_task = asyncio.create_task(simulate_stock_prices())

@app.on_event("shutdown")
async def shutdown_event():
    if background_task:
        background_task.cancel()

# --- Authentication Models and Helper Functions ---
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user_from_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.PyJWTError:
        return None

# --- REST Endpoints ---
@app.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    hashed_password = get_password_hash(user.password)
    success = await create_user(user.username, hashed_password)
    if not success:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "User created successfully"}

@app.post("/login", response_model=Token)
async def login(user: UserCreate):
    db_user = await get_user_by_username(user.username)
    if not db_user or not verify_password(user.password, db_user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user['username']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "username": db_user['username']}

# --- Stock Management Endpoints ---
class StockAdd(BaseModel):
    symbol: str

@app.get("/api/stocks")
async def list_stocks():
    stocks = await get_all_stocks()
    return stocks

@app.post("/api/stocks", status_code=status.HTTP_201_CREATED)
async def track_new_stock(payload: StockAdd):
    symbol = payload.symbol.strip().upper()
    if not symbol or len(symbol) > 10:
        raise HTTPException(status_code=400, detail="Invalid symbol")

    existing = await get_stock_by_symbol(symbol)
    if existing:
        return {"message": "Stock already tracked", "stock": existing}

    initial_price = round(random.uniform(50, 500), 2)
    success = await add_new_stock(symbol, initial_price)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add stock")

    logger.info(f"New stock {symbol} injected into simulation pool at ${initial_price}")
    return {"message": "Stock added", "stock": {"symbol": symbol, "price": initial_price}}

@app.get("/api/stats")
async def system_stats():
    stocks = await get_all_stocks()
    active_tcp = getattr(tcp_manager, 'active_connections', []) if 'tcp_manager' in globals() else []
    return {
        "active_wss_connections": len(manager.active_connections),
        "active_tcp_connections": len(active_tcp),
        "total_tracked_symbols": len(stocks)
    }

# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    # Enforce global rate limiter boundary immediately intercepting prior natively mitigating edge impact
    client_ip = websocket.client.host
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"SECURITY ALERT: Hard rate limit perfectly intercepted spam/malicious attack matching IP {client_ip}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Rate Limit Exceeded")
        return

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return
        
    username = await get_current_user_from_token(token)
    if not username:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    await manager.connect(websocket, username)
    try:
        initial_stocks = await get_all_stocks()
        await websocket.send_text(json.dumps({
            "type": "INIT_STATE",
            "data": initial_stocks
        }))
        
        while True:
            data = await websocket.receive_text()
            pass
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
