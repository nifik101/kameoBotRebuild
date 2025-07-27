import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  LinearProgress,
  Alert,
  Paper,
  CircularProgress,
} from '@mui/material';
import {
  TrendingUp,
  AccountBalance,
  Speed,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material';
import axios from 'axios';

interface SystemStatus {
  database_connected: boolean;
  api_accessible: boolean;
  active_jobs: number;
  total_loans: number;
}

const Dashboard: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSystemStatus();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/system/status');
      setSystemStatus(response.data.data);
      setError(null);
    } catch (err) {
      setError('Kunde inte hämta systemstatus');
      console.error('Error fetching system status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFetchLoans = async () => {
    try {
      await axios.post('/api/loans/fetch');
      fetchSystemStatus(); // Refresh status after fetching
    } catch (err) {
      console.error('Error fetching loans:', err);
    }
  };

  const handleRunDemo = async () => {
    try {
      await axios.post('/api/demo');
    } catch (err) {
      console.error('Error running demo:', err);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Grid container spacing={3}>
        {/* System Status Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <CheckCircle color={systemStatus?.database_connected ? 'success' : 'error'} />
                <Box ml={2}>
                  <Typography variant="h6">Database</Typography>
                  <Chip
                    label={systemStatus?.database_connected ? 'Ansluten' : 'Frånkopplad'}
                    color={systemStatus?.database_connected ? 'success' : 'error'}
                    size="small"
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Speed color={systemStatus?.api_accessible ? 'success' : 'error'} />
                <Box ml={2}>
                  <Typography variant="h6">API</Typography>
                  <Chip
                    label={systemStatus?.api_accessible ? 'Tillgänglig' : 'Otillgänglig'}
                    color={systemStatus?.api_accessible ? 'success' : 'error'}
                    size="small"
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingUp color="primary" />
                <Box ml={2}>
                  <Typography variant="h6">Aktiva Jobb</Typography>
                  <Typography variant="h4">{systemStatus?.active_jobs || 0}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <AccountBalance color="primary" />
                <Box ml={2}>
                  <Typography variant="h6">Totala Lån</Typography>
                  <Typography variant="h4">{systemStatus?.total_loans || 0}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Snabbåtgärder
            </Typography>
            <Box display="flex" gap={2} flexWrap="wrap">
              <Button
                variant="contained"
                color="primary"
                onClick={handleFetchLoans}
                startIcon={<AccountBalance />}
              >
                Hämta Lån
              </Button>
              <Button
                variant="outlined"
                color="secondary"
                onClick={handleRunDemo}
                startIcon={<Speed />}
              >
                Kör Demo
              </Button>
              <Button
                variant="outlined"
                onClick={fetchSystemStatus}
              >
                Uppdatera Status
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Senaste Aktivitet
            </Typography>
            <Box>
              <Alert severity="info" sx={{ mb: 1 }}>
                System startat och redo för användning
              </Alert>
              <Alert severity="success" sx={{ mb: 1 }}>
                Database anslutning etablerad
              </Alert>
              <Alert severity="warning">
                Inga lån har hämtats ännu - klicka "Hämta Lån" för att börja
              </Alert>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;