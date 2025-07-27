"""WebSocket handler for real-time logging and system communication."""

import json
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid


@dataclass
class WebSocketMessage:
    """Structure for WebSocket messages."""
    type: str
    data: Any
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        self.active_connections: Dict[str, Any] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.log_buffer: List[Dict[str, Any]] = []
        self.max_log_buffer = 1000
    
    async def connect(self, websocket) -> str:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        # Generate unique connection ID
        connection_id = str(uuid.uuid4())
        
        # Store connection
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            'connected_at': datetime.now().isoformat(),
            'subscriptions': set(),
        }
        
        # Send connection confirmation
        await self.send_to_connection(
            connection_id,
            WebSocketMessage(
                type='connected',
                data={'connection_id': connection_id, 'message': 'Connected to Kameo Bot WebSocket'}
            )
        )
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]
    
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(asdict(message)))
            except Exception as e:
                print(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_message(self, message: WebSocketMessage):
        """Send a message to all connected clients."""
        if not self.active_connections:
            return
        
        # Store log messages in buffer
        if message.type == 'log':
            self.log_buffer.append(message.data)
            if len(self.log_buffer) > self.max_log_buffer:
                self.log_buffer = self.log_buffer[-self.max_log_buffer:]
        
        # Send to all connections
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(asdict(message)))
            except Exception:
                disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)
    
    async def handle_client_message(self, connection_id: str, message_text: str):
        """Handle incoming message from client."""
        try:
            message_data = json.loads(message_text)
            message_type = message_data.get('type')
            data = message_data.get('data', {})
            
            if message_type == 'request_recent_logs':
                count = data.get('count', 100)
                await self.send_recent_logs(connection_id, count)
                
        except Exception as e:
            print(f"Error handling message from {connection_id}: {e}")
    
    async def send_recent_logs(self, connection_id: str, count: int = 100):
        """Send recent logs to a specific connection."""
        recent_logs = self.log_buffer[-count:] if count else self.log_buffer
        
        for log_entry in recent_logs:
            message = WebSocketMessage(
                type='log',
                data=log_entry
            )
            await self.send_to_connection(connection_id, message)
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all connections."""
        return [
            {
                'connection_id': conn_id,
                'connected_at': metadata['connected_at'],
                'subscriptions': list(metadata['subscriptions'])
            }
            for conn_id, metadata in self.connection_metadata.items()
        ]


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    return websocket_manager
