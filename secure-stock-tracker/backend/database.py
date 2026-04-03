import aiosqlite
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DB_PATH = "stocks.db"

async def init_db():
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("PRAGMA journal_mode=WAL;")
            # Create table for latest stock prices
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol TEXT PRIMARY KEY,
                    price REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create table for price history
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS stock_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    price REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create table for users (auth)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT
                )
            ''')

            # Create table for session logs
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS session_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    event_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Initialize with some default stocks if empty
            async with conn.execute("SELECT count(*) FROM stocks") as cursor:
                row = await cursor.fetchone()
                if row[0] == 0:
                    initial_stocks = [
                        ("AAPL", 150.0),
                        ("GOOGL", 2800.0),
                        ("MSFT", 300.0),
                        ("AMZN", 3300.0),
                        ("TSLA", 700.0)
                    ]
                    await conn.executemany("INSERT INTO stocks (symbol, price) VALUES (?, ?)", initial_stocks)
            
            await conn.commit()
            logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

async def update_stock_price(symbol: str, new_price: float):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute('''
            UPDATE stocks 
            SET price = ?, last_updated = CURRENT_TIMESTAMP
            WHERE symbol = ?
        ''', (new_price, symbol))
        await conn.execute('INSERT INTO stock_prices (symbol, price) VALUES (?, ?)', (symbol, new_price))
        await conn.commit()

async def get_all_stocks() -> List[Dict[str, Any]]:
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT symbol, price, last_updated FROM stocks") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception:
        pass
    return []

async def get_stock_by_symbol(symbol: str) -> Optional[Dict[str, Any]]:
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT symbol, price, last_updated FROM stocks WHERE symbol = ?", (symbol,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    except Exception:
        pass
    return None

async def add_new_stock(symbol: str, initial_price: float) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute('INSERT INTO stocks (symbol, price) VALUES (?, ?)', (symbol, initial_price))
            await conn.execute('INSERT INTO stock_prices (symbol, price) VALUES (?, ?)', (symbol, initial_price))
            await conn.commit()
            return True
    except aiosqlite.IntegrityError:
        return False
    except Exception as e:
        logger.error(f"Error adding stock {symbol}: {e}")
    return False

async def create_user(username: str, password_hash: str) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
            await conn.commit()
            return True
    except aiosqlite.IntegrityError:
        return False
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        
    return False

async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute('SELECT * FROM users WHERE username = ?', (username,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    except Exception:
        pass
    return None

async def log_session_event(username: str, event_type: str):
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute('INSERT INTO session_logs (username, event_type) VALUES (?, ?)', (username, event_type))
            await conn.commit()
    except Exception as e:
        logger.error(f"Error logging session event for {username}: {e}")
