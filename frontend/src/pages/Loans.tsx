import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  Grid,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import { DataGrid, GridColDef, GridToolbar } from '@mui/x-data-grid';
import { Refresh, Download } from '@mui/icons-material';
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

const Loans: React.FC = () => {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchLoans();
  }, []);

  const fetchLoans = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/loans');
      setLoans(response.data.data.loans);
      setError(null);
    } catch (err) {
      setError('Kunde inte hämta lån från databasen');
      console.error('Error fetching loans:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFetchNewLoans = async () => {
    try {
      setLoading(true);
      await axios.post('/api/loans/fetch');
      await fetchLoans(); // Refresh the list
    } catch (err) {
      setError('Kunde inte hämta nya lån från Kameo API');
      console.error('Error fetching new loans:', err);
    }
  };

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'title', headerName: 'Titel', width: 200, flex: 1 },
    {
      field: 'amount',
      headerName: 'Belopp',
      width: 120,
      type: 'number',
      valueFormatter: (params: any) => {
        return params.value ? `${params.value.toLocaleString()} kr` : '';
      },
    },
    {
      field: 'interest_rate',
      headerName: 'Ränta',
      width: 100,
      type: 'number',
      valueFormatter: (params: any) => {
        return params.value ? `${params.value}%` : '';
      },
    },
    {
      field: 'duration',
      headerName: 'Löptid',
      width: 100,
      valueFormatter: (params: any) => {
        return params.value ? `${params.value} mån` : '';
      },
    },
    {
      field: 'risk_grade',
      headerName: 'Riskgrad',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value || 'N/A'}
          color={
            params.value === 'A' ? 'success' :
            params.value === 'B' ? 'primary' :
            params.value === 'C' ? 'warning' : 'error'
          }
          size="small"
        />
      ),
    },
    { field: 'purpose', headerName: 'Syfte', width: 150 },
    { field: 'borrower_name', headerName: 'Låntagare', width: 150 },
    {
      field: 'funded_percentage',
      headerName: 'Finansierad',
      width: 120,
      type: 'number',
      valueFormatter: (params: any) => {
        return params.value ? `${Math.round(params.value)}%` : '0%';
      },
    },
    {
      field: 'created_at',
      headerName: 'Skapad',
      width: 120,
      valueFormatter: (params: any) => {
        return params.value ? new Date(params.value).toLocaleDateString('sv-SE') : '';
      },
    },
  ];

  const filteredLoans = loans.filter(loan =>
    loan.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    loan.borrower_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    loan.purpose?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Lån
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Sök lån..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Sök på titel, låntagare eller syfte"
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <Box display="flex" gap={2}>
            <Button
              variant="contained"
              startIcon={<Refresh />}
              onClick={handleFetchNewLoans}
              disabled={loading}
            >
              Hämta Nya Lån
            </Button>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={fetchLoans}
              disabled={loading}
            >
              Uppdatera
            </Button>
          </Box>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Lån i databasen ({filteredLoans.length} av {loans.length})
            </Typography>
          </Box>

          <Box sx={{ height: 600, width: '100%' }}>
            <DataGrid
              rows={filteredLoans}
              columns={columns}
              loading={loading}
              pageSizeOptions={[25, 50, 100]}
              initialState={{
                pagination: {
                  paginationModel: { pageSize: 25 },
                },
                sorting: {
                  sortModel: [{ field: 'created_at', sort: 'desc' }],
                },
              }}
              slots={{
                toolbar: GridToolbar,
              }}
              slotProps={{
                toolbar: {
                  showQuickFilter: true,
                  quickFilterProps: { debounceMs: 500 },
                },
              }}
              disableRowSelectionOnClick
              sx={{
                '& .MuiDataGrid-cell': {
                  borderBottom: '1px solid rgba(224, 224, 224, 1)',
                },
              }}
            />
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Loans;