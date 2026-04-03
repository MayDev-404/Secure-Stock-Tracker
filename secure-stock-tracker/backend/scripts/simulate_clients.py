import asyncio
import websockets
import json

async def mock_client(client_id, url):
    try:
        import ssl
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        async with websockets.connect(url, ssl=ssl_context) as websocket:
            print(f"Client {client_id} natively established secure linkage!")
            messages_received = 0
            while messages_received < 50:
                await websocket.recv()
                messages_received += 1
            print(f"Client {client_id} gracefully validated {messages_received} live realtime tracking packets mapping dynamically.")
    except Exception as e:
        print(f"Client {client_id} severed: {e}")

async def run_simulation():
    # Install requests globally allowing explicit ignoring of internal TLS mismatches seamlessly
    import sys
    import subprocess
    subprocess.call([sys.executable, "-m", "pip", "install", "requests"], stdout=subprocess.DEVNULL)
    
    import requests, urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("Extracting valid unified token directly bypassing verification logic...")
    try:
        res = requests.post('https://127.0.0.1:8000/login', json={"username": "testuser_123", "password": "password123"}, verify=False)
        token = res.json().get("access_token")
    except Exception as e:
        print(f"Automated Authentication blocked natively resolving pipeline bounds: {e}")
        return
        
    url = f"wss://127.0.0.1:8000/ws?token={token}"
    
    print("Launching Load Testing Protocol natively spawning exactly 40 active socket connections simultaneously tracking parallel throughput bounds!")
    tasks = [mock_client(i, url) for i in range(40)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(run_simulation())
