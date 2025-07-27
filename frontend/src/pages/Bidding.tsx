import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Analytics as AnalyticsIcon,
  Gavel as BidIcon,
} from '@mui/icons-material';
import toast from 'react-hot-toast';
import axios from 'axios';

interface Loan {
  id: number;
  title: string;
  amount: number;
  interest_rate: number;
  duration: number;
  risk_grade: string;
  purpose: string;
  borrower_name: string;
  funded_percentage: number;
  created_at: string;
  updated_at: string;
}

interface SystemStatus {
  database_connected: boolean;
  api_accessible: boolean;
  active_jobs: number;
  total_loans: number;
}

const Bidding: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    database_connected: true,
    api_accessible: true,
    active_jobs: 0,
    total_loans: 0,
  });
  const [loading, setLoading] = useState(false);
  const [availableLoans, setAvailableLoans] = useState<Loan[]>([]);
  const [biddingHistory, setBiddingHistory] = useState<any[]>([]);

  // Load data on mount
  useEffect(() => {
    fetchSystemStatus();
    handleLoadAvailableLoans();
    handleLoadBiddingHistory();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await axios.get('/api/system/status');
      setSystemStatus(response.data.data);
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  const handleLoadAvailableLoans = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/bidding/loans');
      if (response.data.status === 'success' && response.data.data?.loans) {
        setAvailableLoans(response.data.data.loans);
        toast.success(`Hittade ${response.data.data.loans.length} tillgängliga lån`);
      } else {
        setAvailableLoans([]);
        toast.success('Inga tillgängliga lån hittades');
      }
    } catch (error) {
      toast.error('Fel vid hämtning av tillgängliga lån');
      setAvailableLoans([]);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadBiddingHistory = async () => {
    try {
      const response = await axios.get('/api/bidding/history');
      if (response.data.status === 'success' && response.data.data?.history) {
        setBiddingHistory(Array.isArray(response.data.data.history) ? response.data.data.history : []);
      }
    } catch (error) {
      console.log('Kunde inte ladda budhistorik:', error);
      setBiddingHistory([]);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('sv-SE', {
      style: 'currency',
      currency: 'SEK',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Budgivning
        </Typography>
        
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleLoadAvailableLoans}
          disabled={loading}
        >
          Uppdatera
        </Button>
      </Box>

      {/* System Status Warning */}
      {!systemStatus.api_accessible && (
        <Alert severity="error" sx={{ mb: 3 }}>
          API är inte tillgängligt. Budgivning är inte möjlig just nu.
        </Alert>
      )}

      {/* Available Loans */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Tillgängliga Lån för Budgivning ({availableLoans.length})
          </Typography>
          
          {loading && <LinearProgress sx={{ mb: 2 }} />}
          
          {availableLoans.length === 0 ? (
            <Alert severity="info">
              {loading ? 'Laddar tillgängliga lån...' : 'Inga lån tillgängliga för budgivning just nu.'}
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Titel</TableCell>
                    <TableCell align="right">Belopp</TableCell>
                    <TableCell align="right">Ränta</TableCell>
                    <TableCell align="center">Löptid</TableCell>
                    <TableCell align="center">Åtgärder</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {availableLoans.map((loan) => (
                    <TableRow key={loan.id} hover>
                      <TableCell>{loan.id}</TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {loan.title || 'Ingen titel'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        {loan.amount ? formatCurrency(loan.amount) : '-'}
                      </TableCell>
                      <TableCell align="right">
                        {loan.interest_rate ? `${loan.interest_rate}%` : '-'}
                      </TableCell>
                      <TableCell align="center">
                        {loan.duration ? `${loan.duration} mån` : '-'}
                      </TableCell>
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button
                            size="small"
                            startIcon={<AnalyticsIcon />}
                            disabled={loading}
                          >
                            Analysera
                          </Button>
                          <Button
                            size="small"
                            variant="contained"
                            startIcon={<BidIcon />}
                            disabled={loading || !systemStatus.api_accessible}
                          >
                            Buda
                          </Button>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Bidding History */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Budhistorik ({biddingHistory.length})
          </Typography>
          
          <Alert severity="info">
            Budhistorik kommer att visas här när bud har placerats.
          </Alert>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Bidding;
