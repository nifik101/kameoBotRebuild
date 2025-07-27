import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Alert,
  Chip,
  Paper,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Settings,
  Science,
  Save,
  Refresh,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface KameoConfig {
  api_url: string;
  username: string;
  password: string; // This will be hidden in the UI
}

interface DatabaseConfig {
  url: string;
  echo: boolean;
}

interface ConfigData {
  kameo: KameoConfig;
  database: DatabaseConfig;
}

interface TestResult {
  database_connected: boolean;
  api_accessible: boolean;
  message?: string;
}

const Configuration: React.FC = () => {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/config');
      setConfig(response.data.data);
      setError(null);
    } catch (err) {
      setError('Kunde inte hämta konfiguration');
      console.error('Error fetching config:', err);
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      setTesting(true);
      const response = await axios.post('/api/config/test');
      setTestResult(response.data.data);
      setError(null);
    } catch (err) {
      setError('Kunde inte testa anslutningar');
      console.error('Error testing connections:', err);
    } finally {
      setTesting(false);
    }
  };

  const handleConfigChange = (section: keyof ConfigData, field: string, value: any) => {
    if (!config) return;
    
    setConfig(prev => ({
      ...prev!,
      [section]: {
        ...prev![section],
        [field]: value
      }
    }));
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
        Konfiguration
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {successMessage && <Alert severity="success" sx={{ mb: 2 }}>{successMessage}</Alert>}

      <Grid container spacing={3}>
        {/* Kameo API Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Settings />
                <Typography variant="h6">Kameo API</Typography>
              </Box>
              
              {config && (
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="API URL"
                      value={config.kameo.api_url}
                      onChange={(e) => handleConfigChange('kameo', 'api_url', e.target.value)}
                      disabled={true} // Read-only for security
                      helperText="Kameo API endpoint URL (läs endast)"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Användarnamn"
                      value={config.kameo.username}
                      onChange={(e) => handleConfigChange('kameo', 'username', e.target.value)}
                      disabled={true} // Read-only for security
                      helperText="Kameo användarnamn (läs endast)"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Lösenord"
                      type="password"
                      value="••••••••"
                      disabled={true}
                      helperText="Lösenord är dolt av säkerhetsskäl"
                    />
                  </Grid>
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Database Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Settings />
                <Typography variant="h6">Databas</Typography>
              </Box>
              
              {config && (
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Databas URL"
                      value={config.database.url}
                      onChange={(e) => handleConfigChange('database', 'url', e.target.value)}
                      disabled={true} // Read-only for security
                      helperText="SQLite databas sökväg (läs endast)"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Box display="flex" alignItems="center" gap={2}>
                      <Typography>SQL Echo:</Typography>
                      <Chip
                        label={config.database.echo ? 'På' : 'Av'}
                        color={config.database.echo ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                  </Grid>
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Connection Test */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <Science />
              <Typography variant="h6">Anslutningstest</Typography>
            </Box>
            
            <Button
              variant="contained"
              startIcon={testing ? <CircularProgress size={20} /> : <Science />}
              onClick={testConnection}
              disabled={testing}
              sx={{ mb: 2 }}
            >
              {testing ? 'Testar...' : 'Testa Anslutningar'}
            </Button>

            {testResult && (
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Box display="flex" alignItems="center" gap={2}>
                    {testResult.database_connected ? <CheckCircle color="success" /> : <ErrorIcon color="error" />}
                    <Typography>Database:</Typography>
                    <Chip
                      label={testResult.database_connected ? 'Ansluten' : 'Frånkopplad'}
                      color={testResult.database_connected ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box display="flex" alignItems="center" gap={2}>
                    {testResult.api_accessible ? <CheckCircle color="success" /> : <ErrorIcon color="error" />}
                    <Typography>Kameo API:</Typography>
                    <Chip
                      label={testResult.api_accessible ? 'Tillgänglig' : 'Otillgänglig'}
                      color={testResult.api_accessible ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                </Grid>
                {testResult.message && (
                  <Grid item xs={12}>
                    <Alert severity="info">
                      {testResult.message}
                    </Alert>
                  </Grid>
                )}
              </Grid>
            )}
          </Paper>
        </Grid>

        {/* Actions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Åtgärder
            </Typography>
            
            <Box display="flex" gap={2}>
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                onClick={fetchConfig}
                disabled={loading}
              >
                Ladda om konfiguration
              </Button>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Alert severity="info">
              <Typography variant="body2">
                <strong>Säkerhetsnotering:</strong> Konfigurationsinställningar är skrivskyddade i webbgränssnittet av säkerhetsskäl. 
                För att ändra inställningar, uppdatera .env-filen och starta om servern.
              </Typography>
            </Alert>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Configuration;