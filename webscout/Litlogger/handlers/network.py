import asyncio
import json
import socket
from typing import Optional, Dict, Any
import aiohttp
from ..core.level import LogLevel

class NetworkHandler:
    """Handler for sending log messages to a remote server."""
    
    def __init__(
        self,
        host: str,
        port: int,
        protocol: str = "http",
        endpoint: str = "/logs",
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 5.0,
        level: LogLevel = LogLevel.DEBUG,
        batch_size: int = 0,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        custom_fields: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize network handler.
        
        Args:
            host: Remote server hostname/IP
            port: Remote server port
            protocol: 'http', 'https', or 'tcp'
            endpoint: Server endpoint for HTTP/HTTPS
            method: HTTP method to use
            headers: Optional HTTP headers
            timeout: Request timeout in seconds
            level: Minimum log level to send
            batch_size: Number of logs to batch (0 = no batching)
            retry_count: Number of retries on failure
            retry_delay: Delay between retries in seconds
            custom_fields: Additional fields to include in log data
        """
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self.endpoint = endpoint
        self.method = method.upper()
        self.headers = headers or {}
        self.timeout = timeout
        self.level = level
        self.batch_size = batch_size
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.custom_fields = custom_fields or {}
        
        if self.protocol not in ["http", "https", "tcp"]:
            raise ValueError("Protocol must be 'http', 'https' or 'tcp'")
            
        self._batch = []
        self._tcp_socket = None
        self._session = None
        
    async def _init_session(self):
        """Initialize HTTP session if needed."""
        if self.protocol in ["http", "https"] and not self._session:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            
    async def _send_http(self, data: Dict[str, Any]) -> bool:
        """Send log data via HTTP/HTTPS."""
        await self._init_session()
        
        url = f"{self.protocol}://{self.host}:{self.port}{self.endpoint}"
        
        for attempt in range(self.retry_count + 1):
            try:
                async with self._session.request(
                    method=self.method,
                    url=url,
                    json=data,
                    headers=self.headers
                ) as response:
                    return response.status < 400
                    
            except Exception:
                if attempt == self.retry_count:
                    return False
                await asyncio.sleep(self.retry_delay)
                
    async def _send_tcp(self, data: Dict[str, Any]) -> bool:
        """Send log data via TCP."""
        message = json.dumps(data).encode() + b"\n"
        
        for attempt in range(self.retry_count + 1):
            try:
                if not self._tcp_socket:
                    self._tcp_socket = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM
                    )
                    self._tcp_socket.settimeout(self.timeout)
                    self._tcp_socket.connect((self.host, self.port))
                    
                self._tcp_socket.sendall(message)
                return True
                
            except Exception:
                if self._tcp_socket:
                    self._tcp_socket.close()
                    self._tcp_socket = None
                    
                if attempt == self.retry_count:
                    return False
                    
                await asyncio.sleep(self.retry_delay)
                
    def emit(self, message: str, level: LogLevel):
        """
        Synchronously send log message.
        Not recommended - use async_emit instead.
        """
        if level.value >= self.level.value:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.async_emit(message, level))
            
    async def async_emit(self, message: str, level: LogLevel):
        """Asynchronously send log message to remote server."""
        # Fix: Allow all messages if level is NOTSET
        if self.level == LogLevel.NOTSET or level.value >= self.level.value:
            log_data = {
                "message": message,
                "level": level.name,
                **self.custom_fields
            }
            
            if self.batch_size > 0:
                self._batch.append(log_data)
                if len(self._batch) >= self.batch_size:
                    await self._send_batch()
            else:
                if self.protocol in ["http", "https"]:
                    await self._send_http(log_data)
                else:
                    await self._send_tcp(log_data)
                    
    async def _send_batch(self):
        """Send batched log messages."""
        if not self._batch:
            return
            
        batch_data = {"logs": self._batch}
        success = False
        
        if self.protocol in ["http", "https"]:
            success = await self._send_http(batch_data)
        else:
            success = await self._send_tcp(batch_data)
            
        if success:
            self._batch.clear()
            
    async def close(self):
        """Close network connections."""
        if self._batch:
            await self._send_batch()
            
        if self._tcp_socket:
            self._tcp_socket.close()
            self._tcp_socket = None
            
        if self._session:
            await self._session.close()
            self._session = None
