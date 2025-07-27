import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
  IconButton,
  TextField,
  Grid,
  Alert,
} from '@mui/material';
import {
  Clear,
  PlayArrow,
  Stop,
  Send,
  Terminal as TerminalIcon,
} from '@mui/icons-material';

interface LogMessage {
  id: string;
  timestamp: string;
  level: string;
  message: string;
  source?: string;
}

const Terminal: React.FC = () => {
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<string>('Disconnected');
  const [command, setCommand] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);

  const connectWebSocket = () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;
      const websocket = new WebSocket(wsUrl);

      websocket.onopen = () => {
        setConnected(true);
        setConnectionStatus('Connected');
        addLog('info', 'WebSocket connection established');
        
        // Subscribe to logs
        websocket.send('subscribe_logs');
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'log') {
            addLog(data.level || 'info', data.message, data.source);
          } else {
            addLog('info', event.data);
          }
        } catch {
          // If not JSON, treat as plain message
          addLog('info', event.data);
        }
      };

      websocket.onclose = () => {
        setConnected(false);
        setConnectionStatus('Disconnected');
        addLog('warning', 'WebSocket connection closed');
      };

      websocket.onerror = (error) => {
        setConnected(false);
        setConnectionStatus('Error');
        addLog('error', 'WebSocket error occurred');
        console.error('WebSocket error:', error);
      };

      setWs(websocket);
    } catch (error) {
      setConnectionStatus('Error');
      addLog('error', 'Failed to connect to WebSocket');
      console.error('WebSocket connection error:', error);
    }
  };

  const disconnectWebSocket = () => {
    if (ws) {
      ws.close();
      setWs(null);
    }
  };

  const addLog = (level: string, message: string, source?: string) => {
    const logMessage: LogMessage = {
      id: Date.now().toString() + Math.random(),
      timestamp: new Date().toLocaleTimeString('sv-SE'),
      level,
      message,
      source,
    };
    
    setLogs(prev => [...prev, logMessage]);
  };

  const clearLogs = () => {
    setLogs([]);
  };

  const sendCommand = () => {
    if (ws && connected && command.trim()) {
      ws.send(command);
      addLog('info', `Command sent: ${command}`, 'client');
      setCommand('');
    }
  };

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
        return 'error';
      case 'warning':
      case 'warn':
        return 'warning';
      case 'info':
        return 'info';
      case 'debug':
        return 'default';
      default:
        return 'default';
    }
  };

  useEffect(() => {
    // Auto-scroll to bottom when new logs are added
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    // Auto-connect on component mount
    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Terminal
      </Typography>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={6}>
          <Box display="flex" alignItems="center" gap={2}>
            <TerminalIcon />
            <Typography variant="h6">WebSocket Terminal</Typography>
            <Chip
              label={connectionStatus}
              color={connected ? 'success' : 'error'}
              size="small"
            />
          </Box>
        </Grid>
        <Grid item xs={12} md={6}>
          <Box display="flex" gap={1} justifyContent="flex-end">
            {!connected ? (
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={connectWebSocket}
                color="success"
              >
                Anslut
              </Button>
            ) : (
              <Button
                variant="contained"
                startIcon={<Stop />}
                onClick={disconnectWebSocket}
                color="error"
              >
                Koppla från
              </Button>
            )}
            <Button
              variant="outlined"
              startIcon={<Clear />}
              onClick={clearLogs}
            >
              Rensa
            </Button>
          </Box>
        </Grid>
      </Grid>

      {!connected && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Inte ansluten till WebSocket. Klicka "Anslut" för att se realtidsloggar.
        </Alert>
      )}

      {/* Command Input */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs>
            <TextField
              fullWidth
              size="small"
              placeholder="Skriv kommando... (t.ex. 'subscribe_logs', 'unsubscribe_logs')"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  sendCommand();
                }
              }}
              disabled={!connected}
            />
          </Grid>
          <Grid item>
            <IconButton
              color="primary"
              onClick={sendCommand}
              disabled={!connected || !command.trim()}
            >
              <Send />
            </IconButton>
          </Grid>
        </Grid>
      </Paper>

      {/* Log Display */}
      <Paper sx={{ height: 500, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Box
          sx={{
            p: 1,
            borderBottom: 1,
            borderColor: 'divider',
            bgcolor: 'grey.50',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <Typography variant="subtitle2" color="text.secondary">
            Loggar ({logs.length})
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Senaste meddelanden visas längst ner
          </Typography>
        </Box>
        
        <Box
          ref={logContainerRef}
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 1,
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            backgroundColor: '#1e1e1e',
            color: '#d4d4d4',
          }}
        >
          {logs.length === 0 ? (
            <Box
              display="flex"
              alignItems="center"
              justifyContent="center"
              height="100%"
              color="text.secondary"
            >
              <Typography variant="body2">
                Inga loggar än. Anslut till WebSocket för att börja ta emot loggar.
              </Typography>
            </Box>
          ) : (
            logs.map((log) => (
              <Box key={log.id} sx={{ mb: 0.5, display: 'flex', gap: 1 }}>
                <Typography
                  component="span"
                  sx={{
                    color: '#569cd6',
                    minWidth: '80px',
                    fontSize: '0.75rem'
                  }}
                >
                  [{log.timestamp}]
                </Typography>
                <Chip
                  label={log.level.toUpperCase()}
                  size="small"
                  color={getLevelColor(log.level) as any}
                  sx={{ minWidth: '60px', height: '20px', fontSize: '0.7rem' }}
                />
                {log.source && (
                  <Typography
                    component="span"
                    sx={{ color: '#ce9178', fontSize: '0.75rem' }}
                  >
                    [{log.source}]
                  </Typography>
                )}
                <Typography
                  component="span"
                  sx={{
                    color: log.level === 'error' ? '#f48771' : 
                           log.level === 'warning' ? '#dcdcaa' : '#d4d4d4',
                    wordBreak: 'break-word',
                    flex: 1
                  }}
                >
                  {log.message}
                </Typography>
              </Box>
            ))
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default Terminal;