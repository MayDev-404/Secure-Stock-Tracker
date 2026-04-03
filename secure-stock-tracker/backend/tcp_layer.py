import asyncio
import socket
import logging
import json

logger = logging.getLogger(__name__)

class TCPConnectionManager:
    def __init__(self):
        self.active_connections = set()

    async def broadcast(self, message: str):
        # Handle broadcasting stock updates to all raw TCP clients
        encoded_msg = (message + "\\n").encode('utf-8')
        for writer in list(self.active_connections):
            try:
                # Log the intent to send reflecting the transport phase
                peer_name = writer.get_extra_info('peername')
                logger.info(f"TCP SEND: preparing to transmit {len(encoded_msg)} bytes to {peer_name}")
                
                # Manual application layer buffering. writer.write buffers in memory.
                writer.write(encoded_msg)
                
                # Drain blocks until the send buffer naturally empties over the network. 
                # Essential for gracefully resolving partial sends caused by saturated TCP windows.
                await writer.drain() 
            except Exception as e:
                peer = writer.get_extra_info('peername')
                logger.error(f"TCP SEND ERROR: Removing blocked client {peer}: {e}")
                self.disconnect(writer)

    def disconnect(self, writer: asyncio.StreamWriter):
        if writer in self.active_connections:
            self.active_connections.remove(writer)
            try:
                writer.close()
            except:
                pass

tcp_manager = TCPConnectionManager()

async def handle_tcp_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    peer_name = writer.get_extra_info('peername')
    logger.info(f"TCP ACCEPT: New connection established with {peer_name}")
    
    # 1. Retrieve the underlying raw socket object to hack the Posix primitives directly
    sock = writer.get_extra_info('socket')
    if sock is not None:
        try:
            # 2. Configure low-level socket options to demonstrate OS-level optimizations
            
            # TCP_NODELAY (Disable Nagle's algorithm)
            # Instructs the TCP stack to flush small fragments (stock ticks) instantly without batching.
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            logger.info(f"TCP SOCKET OPTION: SO_NODELAY enabled for {peer_name} (Optimizing for low latency streams).")
            
            # SO_KEEPALIVE
            # Enforces periodic empty heartbeat probes to aggressively detect ungracefully severed connections/dead peers.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            logger.info(f"TCP SOCKET OPTION: SO_KEEPALIVE enabled for {peer_name} (Preventing silent socket drops).")
            
            # SO_SNDBUF / SO_RCVBUF
            # Overrides network buffer bounds per client socket to cap memory consumption.
            buffer_size = 16384  # 16KB budget per socket
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_size)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
            logger.info(f"TCP SOCKET OPTION: SO_SNDBUF and SO_RCVBUF strictly constrained to {buffer_size} bytes for {peer_name}.")

        except Exception as e:
            logger.error(f"TCP CONFIG ERROR: Failed to toggle socket syscalls for {peer_name}: {e}")

    tcp_manager.active_connections.add(writer)
    
    try:
        # 3. Stream reader loop to prove partial receive capability 
        while True:
            # Reading network stream iteratively in distinct 1024-byte chunks
            # A client blasting a massive payload will be safely parsed in partial chunks.
            chunk = await reader.read(1024)
            
            if not chunk:
                # EOF reached. Client terminated the connection elegantly via FIN packet.
                logger.info(f"TCP EOF: Connection cleanly terminated stream by {peer_name}")
                break
                
            # Log exact payload volume to represent TCP's unpredictable byte-oriented architecture
            logger.info(f"TCP RECV: Decoded {len(chunk)} inbound application bytes from {peer_name} via stream buffer")
            
    except ConnectionResetError:
        # Client terminated violently via an RST packet rather than standard teardown sequence.
        logger.warning(f"TCP RST: Connection abruptly reset by peer {peer_name}")
    except Exception as e:
        logger.error(f"TCP ERROR: Catastrophic exception on stream {peer_name}: {e}")
    finally:
        # 4. Cleanup the socket cleanly (TCP CLOSE phase) destroying all file descriptors
        logger.info(f"TCP CLOSE: Tearing down state machine entirely for {peer_name}")
        tcp_manager.disconnect(writer)

async def start_custom_tcp_server():
    # BIND and LISTEN phases: Initialize an asyncio raw socket listener mapped directly over the host interfaces
    # reuse_address=True perfectly mimics the `socket.SO_REUSEADDR` flag allowing us to rebind the port quickly without OS block (TIME_WAIT trap bypass)
    server = await asyncio.start_server(
        handle_tcp_client, 
        host="0.0.0.0", 
        port=8001,
        reuse_address=True
    )
    
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logger.info(f"TCP BIND/LISTEN: Underlying core TCP Server aggressively LISTENING on {addrs} (SO_REUSEADDR enabled implicitly)")
    
    async with server:
        await server.serve_forever()
