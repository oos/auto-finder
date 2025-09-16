import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import styled from 'styled-components';
import axios from 'axios';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: ${props => props.theme.spacing.lg};
`;

const Title = styled.h1`
  color: ${props => props.theme.colors.primary};
  margin-bottom: ${props => props.theme.spacing.xl};
`;

const Section = styled.div`
  background: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.lg};
  border-radius: ${props => props.theme.borderRadius};
  box-shadow: ${props => props.theme.boxShadow};
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const SectionTitle = styled.h2`
  color: ${props => props.theme.colors.primary};
  margin-bottom: ${props => props.theme.spacing.lg};
  font-size: 1.3rem;
`;

const StatusCard = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: ${props => props.theme.spacing.lg};
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const StatusItem = styled.div`
  text-align: center;
  padding: ${props => props.theme.spacing.lg};
  border-radius: ${props => props.theme.borderRadius};
  background: ${props => {
    switch (props.status) {
      case 'running': return '#fff3cd';
      case 'completed': return '#d4edda';
      case 'failed': return '#f8d7da';
      case 'blocked': return '#f5c6cb';
      default: return '#f8f9fa';
    }
  }};
  border: 2px solid ${props => {
    switch (props.status) {
      case 'running': return '#ffeaa7';
      case 'completed': return '#c3e6cb';
      case 'failed': return '#f1b0b7';
      case 'blocked': return '#f1aeb5';
      default: return '#dee2e6';
    }
  }};
`;

const StatusValue = styled.div`
  font-size: 2rem;
  font-weight: bold;
  color: ${props => props.theme.colors.primary};
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const StatusLabel = styled.div`
  color: ${props => props.theme.colors.gray};
  font-weight: 500;
`;

const Button = styled.button`
  background: ${props => {
    switch (props.variant) {
      case 'danger': return props.theme.colors.danger;
      case 'success': return props.theme.colors.success;
      default: return props.theme.colors.secondary;
    }
  }};
  color: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.md} ${props => props.theme.spacing.lg};
  border-radius: ${props => props.theme.borderRadius};
  border: none;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-right: ${props => props.theme.spacing.md};
  margin-bottom: ${props => props.theme.spacing.md};
  
  &:hover {
    background: ${props => {
      switch (props.variant) {
        case 'danger': return '#c0392b';
        case 'success': return '#229954';
        default: return '#2980b9';
      }
    }};
  }
  
  &:disabled {
    background: ${props => props.theme.colors.lightGray};
    cursor: not-allowed;
  }
`;

const LogsTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-top: ${props => props.theme.spacing.lg};
`;

const TableHeader = styled.th`
  background: ${props => props.theme.colors.light};
  padding: ${props => props.theme.spacing.md};
  text-align: left;
  font-weight: 500;
  color: ${props => props.theme.colors.dark};
  border-bottom: 2px solid ${props => props.theme.colors.lightGray};
`;

const TableCell = styled.td`
  padding: ${props => props.theme.spacing.md};
  border-bottom: 1px solid ${props => props.theme.colors.lightGray};
`;

const StatusBadge = styled.span`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  font-size: 0.8rem;
  font-weight: 500;
  background: ${props => {
    switch (props.status) {
      case 'running': return '#fff3cd';
      case 'completed': return '#d4edda';
      case 'failed': return '#f8d7da';
      case 'blocked': return '#f5c6cb';
      case 'stopped': return '#e2e3e5';
      default: return '#f8f9fa';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'running': return '#856404';
      case 'completed': return '#155724';
      case 'failed': return '#721c24';
      case 'blocked': return '#721c24';
      case 'stopped': return '#383d41';
      default: return '#6c757d';
    }
  }};
`;

const Checkbox = styled.input`
  width: 18px;
  height: 18px;
  cursor: pointer;
`;

const CheckboxCell = styled.td`
  padding: ${props => props.theme.spacing.md};
  border-bottom: 1px solid ${props => props.theme.colors.lightGray};
  text-align: center;
  width: 50px;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  font-size: 1.2rem;
  color: ${props => props.theme.colors.gray};
`;

const ErrorMessage = styled.div`
  background: #fee;
  color: ${props => props.theme.colors.danger};
  padding: ${props => props.theme.spacing.lg};
  border-radius: ${props => props.theme.borderRadius};
  text-align: center;
  margin: ${props => props.theme.spacing.lg} 0;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: ${props => props.theme.spacing.xl};
  color: ${props => props.theme.colors.gray};
  background: ${props => props.theme.colors.light};
  border-radius: ${props => props.theme.borderRadius};
  margin: ${props => props.theme.spacing.lg} 0;
`;

const EmptyStateIcon = styled.div`
  font-size: 3rem;
  margin-bottom: ${props => props.theme.spacing.md};
  opacity: 0.5;
`;

const EmptyStateTitle = styled.h3`
  color: ${props => props.theme.colors.dark};
  margin-bottom: ${props => props.theme.spacing.sm};
  font-size: 1.2rem;
`;

const EmptyStateText = styled.p`
  color: ${props => props.theme.colors.gray};
  margin: 0;
  line-height: 1.5;
`;

const InfoBox = styled.div`
  background: #e7f3ff;
  color: #0066cc;
  padding: ${props => props.theme.spacing.lg};
  border-radius: ${props => props.theme.borderRadius};
  border: 1px solid #b3d9ff;
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const LoginForm = styled.div`
  background: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.xl};
  border-radius: ${props => props.theme.borderRadius};
  box-shadow: ${props => props.theme.boxShadow};
  max-width: 400px;
  margin: 0 auto;
  text-align: center;
`;

const FormTitle = styled.h2`
  color: ${props => props.theme.colors.primary};
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const FormGroup = styled.div`
  margin-bottom: ${props => props.theme.spacing.lg};
  text-align: left;
`;

const Label = styled.label`
  display: block;
  margin-bottom: ${props => props.theme.spacing.sm};
  color: ${props => props.theme.colors.dark};
  font-weight: 500;
`;

const Input = styled.input`
  width: 100%;
  padding: ${props => props.theme.spacing.md};
  border: 1px solid ${props => props.theme.colors.lightGray};
  border-radius: ${props => props.theme.borderRadius};
  font-size: 1rem;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const LoginButton = styled.button`
  width: 100%;
  background: ${props => props.theme.colors.primary};
  color: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.md};
  border: none;
  border-radius: ${props => props.theme.borderRadius};
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: #2980b9;
  }
  
  &:disabled {
    background: ${props => props.theme.colors.lightGray};
    cursor: not-allowed;
  }
`;

const TestButton = styled.button`
  background: #27ae60;
  color: white;
  padding: ${props => props.theme.spacing.md} ${props => props.theme.spacing.lg};
  border: none;
  border-radius: ${props => props.theme.borderRadius};
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  margin: ${props => props.theme.spacing.md};
  transition: all 0.2s ease;
  
  &:hover {
    background: #229954;
  }
  
  &:disabled {
    background: ${props => props.theme.colors.lightGray};
    cursor: not-allowed;
  }
`;

const Scraping = () => {
  const queryClient = useQueryClient();
  const { user, login } = useAuth();
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [selectedRows, setSelectedRows] = useState(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Fetch scraping status
  const { data: status, isLoading: statusLoading, error: statusError } = useQuery(
    'scraping-status',
    () => axios.get('/api/scraping/status').then(res => res.data),
    { refetchInterval: 5000 } // Refetch every 5 seconds
  );

  // Fetch scraping logs
  const { data: logs, isLoading: logsLoading, error: logsError, refetch: refetchLogs } = useQuery(
    'scraping-logs',
    () => axios.get('/api/scraping/logs?per_page=50').then(res => res.data)
  );

  // Fetch scraping health status
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useQuery(
    'scraping-health',
    () => axios.get('/api/scraping/monitor/health').then(res => res.data),
    { refetchInterval: 30000 } // Refetch every 30 seconds
  );

  // Fetch scraping statistics
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery(
    'scraping-stats',
    () => axios.get('/api/scraping/monitor/stats?days=7').then(res => res.data)
  );

  // Start scraping mutation
  const startScrapingMutation = useMutation(
    () => axios.post('/api/scraping/start'),
    {
      onSuccess: (response) => {
        const data = response.data;
        toast.success(`Real scraping started! Found ${data.listings_found || 0} listings`);
        queryClient.invalidateQueries('scraping-status');
        queryClient.invalidateQueries('scraping-logs');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to start scraping');
      },
    }
  );

  // Stop scraping mutation
  const stopScrapingMutation = useMutation(
    () => axios.post('/api/scraping/stop'),
    {
      onSuccess: () => {
        toast.success('Scraping stopped successfully!');
        queryClient.invalidateQueries('scraping-status');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to stop scraping');
      },
    }
  );

  // Delete failed scrapes mutation
  const deleteFailedMutation = useMutation(
    () => axios.post('/api/scraping/delete-failed'),
    {
      onSuccess: (response) => {
        toast.success(`Deleted ${response.data.failed_logs_deleted} failed scrapes!`);
        queryClient.invalidateQueries('scraping-status');
        queryClient.invalidateQueries('scraping-logs');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to delete failed scrapes');
      },
    }
  );

  // Bulk delete selected scrapes mutation
  const bulkDeleteMutation = useMutation(
    (selectedIds) => axios.post('/api/scraping/bulk-delete', { ids: Array.from(selectedIds) }),
    {
      onSuccess: (response) => {
        toast.success(`Deleted ${response.data.deleted_count} selected scrapes!`);
        setSelectedRows(new Set());
        setSelectAll(false);
        queryClient.invalidateQueries('scraping-status');
        queryClient.invalidateQueries('scraping-logs');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to delete selected scrapes');
      },
    }
  );

  // Test scraping mutation
  const testScrapingMutation = useMutation(
    (site) => axios.post('/api/scraping/test', { site }),
    {
      onSuccess: (response) => {
        const data = response.data;
        toast.success(`Test completed for ${data.site_tested}! Found ${data.listings_found} listings`);
        queryClient.invalidateQueries('scraping-logs');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Test failed');
      },
    }
  );

  // Run test suite mutation
  const testSuiteMutation = useMutation(
    () => axios.post('/api/scraping/monitor/test-suite'),
    {
      onSuccess: (response) => {
        toast.success('Test suite completed successfully!');
        queryClient.invalidateQueries('scraping-health');
        queryClient.invalidateQueries('scraping-stats');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Test suite failed');
      },
    }
  );

  // Cleanup old data mutation
  const cleanupMutation = useMutation(
    (daysOld) => axios.post('/api/scraping/monitor/cleanup', { days_old: daysOld }),
    {
      onSuccess: (response) => {
        const data = response.data;
        toast.success(`Cleanup completed! Removed ${data.total_cleaned} old records`);
        queryClient.invalidateQueries('scraping-logs');
        queryClient.invalidateQueries('scraping-stats');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Cleanup failed');
      },
    }
  );

  const handleStartScraping = async () => {
    setIsStarting(true);
    try {
      await startScrapingMutation.mutateAsync();
    } finally {
      setIsStarting(false);
    }
  };

  const handleStopScraping = async () => {
    setIsStopping(true);
    try {
      await stopScrapingMutation.mutateAsync();
    } finally {
      setIsStopping(false);
    }
  };

  const handleDeleteFailed = async () => {
    if (window.confirm('Are you sure you want to delete all failed scraping attempts? This action cannot be undone.')) {
      await deleteFailedMutation.mutateAsync();
    }
  };

  const handleSelectRow = (logId) => {
    const newSelected = new Set(selectedRows);
    if (newSelected.has(logId)) {
      newSelected.delete(logId);
    } else {
      newSelected.add(logId);
    }
    setSelectedRows(newSelected);
    setSelectAll(newSelected.size === logs?.logs?.length);
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedRows(new Set());
      setSelectAll(false);
    } else {
      const allIds = new Set(logs?.logs?.map(log => log.id) || []);
      setSelectedRows(allIds);
      setSelectAll(true);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedRows.size === 0) {
      toast.error('Please select at least one row to delete');
      return;
    }
    
    if (window.confirm(`Are you sure you want to delete ${selectedRows.size} selected scraping attempts? This action cannot be undone.`)) {
      await bulkDeleteMutation.mutateAsync(selectedRows);
    }
  };

  const handleRefresh = async () => {
    try {
      await Promise.all([
        queryClient.invalidateQueries('scraping-status'),
        refetchLogs(),
        refetchHealth(),
        refetchStats()
      ]);
      toast.success('Data refreshed successfully!');
    } catch (error) {
      toast.error('Failed to refresh data');
    }
  };

  const handleTestScraping = async (site) => {
    await testScrapingMutation.mutateAsync(site);
  };

  const handleRunTestSuite = async () => {
    await testSuiteMutation.mutateAsync();
  };

  const handleCleanup = async () => {
    if (window.confirm('Are you sure you want to clean up old data? This will remove logs and listings older than 30 days.')) {
      await cleanupMutation.mutateAsync(30);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoggingIn(true);
    try {
      const result = await login(loginForm.email, loginForm.password);
      if (result.success) {
        toast.success('Login successful! You can now use the scraping features.');
        setLoginForm({ email: '', password: '' });
      }
    } catch (error) {
      toast.error('Login failed. Please try again.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handlePublicTest = async (site) => {
    try {
      const response = await axios.post('/api/scraping/test-public', { site });
      toast.success(`Public test completed! Found ${response.data.listings_found} listings from ${site}`);
    } catch (error) {
      toast.error(`Public test failed: ${error.response?.data?.error || error.message}`);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (startedAt, completedAt) => {
    if (!startedAt) return 'N/A';
    
    const start = new Date(startedAt);
    const end = completedAt ? new Date(completedAt) : new Date();
    const duration = Math.floor((end - start) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  // Show login form if not authenticated
  if (!user) {
    return (
      <Container>
        <Title>Scraping Management</Title>
        
        <InfoBox>
          <strong>Authentication Required:</strong> You need to be logged in to use the scraping features. 
          Please log in below or use the public test buttons to test the scraping functionality.
        </InfoBox>

        <LoginForm>
          <FormTitle>Login to Access Scraping</FormTitle>
          <form onSubmit={handleLogin}>
            <FormGroup>
              <Label htmlFor="email">Email</Label>
              <Input
                type="email"
                id="email"
                value={loginForm.email}
                onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                required
                placeholder="Enter your email"
              />
            </FormGroup>
            <FormGroup>
              <Label htmlFor="password">Password</Label>
              <Input
                type="password"
                id="password"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                required
                placeholder="Enter your password"
              />
            </FormGroup>
            <LoginButton type="submit" disabled={isLoggingIn}>
              {isLoggingIn ? 'Logging in...' : 'Login'}
            </LoginButton>
          </form>
        </LoginForm>

        <Section>
          <SectionTitle>Public Test (No Login Required)</SectionTitle>
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
            <TestButton onClick={() => handlePublicTest('carzone')}>
              Test Carzone Scraping
            </TestButton>
            <TestButton onClick={() => handlePublicTest('donedeal')}>
              Test DoneDeal Scraping
            </TestButton>
          </div>
          <InfoBox style={{ marginTop: '2rem' }}>
            <strong>Note:</strong> Public tests are limited and don't save data to the database. 
            For full functionality, please log in above.
          </InfoBox>
        </Section>
      </Container>
    );
  }

  if (statusLoading) {
    return (
      <Container>
        <LoadingSpinner>Loading scraping status...</LoadingSpinner>
      </Container>
    );
  }

  if (statusError) {
    return (
      <Container>
        <ErrorMessage>
          Error loading scraping status. Please try again later.
        </ErrorMessage>
      </Container>
    );
  }

  const isRunning = status?.is_running || false;
  const runningScrapes = status?.running_scrapes || [];
  const recentLogs = status?.recent_logs || [];

  return (
    <Container>
      <Title>Scraping Management</Title>

      <InfoBox>
        <strong>Real Web Scraping System:</strong> This system scrapes live car listings from Irish websites (Carzone.ie, DoneDeal.ie). 
        It processes real data, detects duplicates, calculates deal scores, and stores everything in the database. 
        Use the monitoring tools below to check system health and performance.
      </InfoBox>

      {/* System Health */}
      {health && (
        <Section>
          <SectionTitle>System Health</SectionTitle>
          <StatusCard>
            <StatusItem status={health.overall_status === 'healthy' ? 'completed' : 'failed'}>
              <StatusValue>{health.overall_status === 'healthy' ? '✅' : '❌'}</StatusValue>
              <StatusLabel>
                {health.overall_status === 'healthy' ? 'All Systems Healthy' : 'System Issues Detected'}
              </StatusLabel>
            </StatusItem>
            
            {health.sites && Object.entries(health.sites).map(([site, siteHealth]) => (
              <StatusItem key={site} status={siteHealth.status === 'healthy' ? 'completed' : 'failed'}>
                <StatusValue>{siteHealth.accessible ? '🌐' : '🚫'}</StatusValue>
                <StatusLabel>
                  {site.charAt(0).toUpperCase() + site.slice(1)}
                  {siteHealth.response_time && (
                    <div style={{ fontSize: '0.8rem', color: '#666' }}>
                      {siteHealth.response_time.toFixed(2)}s
                    </div>
                  )}
                </StatusLabel>
              </StatusItem>
            ))}
          </StatusCard>
        </Section>
      )}

      {/* Current Status */}
      <Section>
        <SectionTitle>Current Status</SectionTitle>
        <StatusCard>
          <StatusItem status={isRunning ? 'running' : 'completed'}>
            <StatusValue>{isRunning ? '🔄' : '✅'}</StatusValue>
            <StatusLabel>
              {isRunning ? 'Scraping in Progress' : 'Idle'}
            </StatusLabel>
          </StatusItem>
          
          <StatusItem>
            <StatusValue>{runningScrapes.length}</StatusValue>
            <StatusLabel>Active Jobs</StatusLabel>
          </StatusItem>
          
          <StatusItem>
            <StatusValue>{recentLogs.length}</StatusValue>
            <StatusLabel>Recent Jobs</StatusLabel>
          </StatusItem>
        </StatusCard>

        <div>
          <Button
            onClick={handleStartScraping}
            disabled={isStarting || isRunning}
            variant="success"
          >
            {isStarting ? 'Starting...' : 'Start Scraping'}
          </Button>
          
          <Button
            onClick={handleStopScraping}
            disabled={isStopping || !isRunning}
            variant="danger"
          >
            {isStopping ? 'Stopping...' : 'Stop Scraping'}
          </Button>
          
          <Button
            onClick={handleDeleteFailed}
            disabled={deleteFailedMutation.isLoading}
            variant="danger"
            style={{ backgroundColor: '#e74c3c' }}
          >
            {deleteFailedMutation.isLoading ? 'Deleting...' : 'Delete Failed Scrapes'}
          </Button>
          
          <Button
            onClick={handleBulkDelete}
            disabled={bulkDeleteMutation.isLoading || selectedRows.size === 0}
            variant="danger"
            style={{ backgroundColor: '#8e44ad' }}
          >
            {bulkDeleteMutation.isLoading ? 'Deleting...' : `Delete Selected (${selectedRows.size})`}
          </Button>
          
          <Button
            onClick={handleRefresh}
            variant="success"
            style={{ backgroundColor: '#27ae60' }}
          >
            🔄 Refresh Data
          </Button>
          
          <Button
            onClick={() => handleTestScraping('carzone')}
            disabled={testScrapingMutation.isLoading}
            variant="success"
            style={{ backgroundColor: '#3498db' }}
          >
            {testScrapingMutation.isLoading ? 'Testing...' : 'Test Carzone'}
          </Button>
          
          <Button
            onClick={() => handleTestScraping('donedeal')}
            disabled={testScrapingMutation.isLoading}
            variant="success"
            style={{ backgroundColor: '#9b59b6' }}
          >
            {testScrapingMutation.isLoading ? 'Testing...' : 'Test DoneDeal'}
          </Button>
          
          <Button
            onClick={handleRunTestSuite}
            disabled={testSuiteMutation.isLoading}
            variant="success"
            style={{ backgroundColor: '#e67e22' }}
          >
            {testSuiteMutation.isLoading ? 'Running...' : 'Run Test Suite'}
          </Button>
          
          <Button
            onClick={handleCleanup}
            disabled={cleanupMutation.isLoading}
            variant="danger"
            style={{ backgroundColor: '#e74c3c' }}
          >
            {cleanupMutation.isLoading ? 'Cleaning...' : 'Cleanup Old Data'}
          </Button>
        </div>
      </Section>

      {/* Running Jobs */}
      {runningScrapes.length > 0 && (
        <Section>
          <SectionTitle>Currently Running</SectionTitle>
          <LogsTable>
            <thead>
              <tr>
                <TableHeader>Site</TableHeader>
                <TableHeader>Started</TableHeader>
                <TableHeader>Duration</TableHeader>
                <TableHeader>Status</TableHeader>
                <TableHeader>Progress</TableHeader>
              </tr>
            </thead>
            <tbody>
              {runningScrapes.map((log) => (
                <tr key={log.id}>
                  <TableCell>{log.site_name}</TableCell>
                  <TableCell>{formatDate(log.started_at)}</TableCell>
                  <TableCell>{formatDuration(log.started_at, log.completed_at)}</TableCell>
                  <TableCell>
                    <StatusBadge status={log.status}>
                      {log.status.toUpperCase()}
                    </StatusBadge>
                  </TableCell>
                  <TableCell>
                    {log.pages_scraped} pages, {log.listings_found} listings
                  </TableCell>
                </tr>
              ))}
            </tbody>
          </LogsTable>
        </Section>
      )}

      {/* Recent Logs */}
      <Section>
        <SectionTitle>Recent Scraping Logs</SectionTitle>
        {logsLoading ? (
          <LoadingSpinner>Loading logs...</LoadingSpinner>
        ) : logsError ? (
          <ErrorMessage>Error loading logs. Please try again later.</ErrorMessage>
        ) : logs?.logs?.length === 0 ? (
          <EmptyState>
            <EmptyStateIcon>📊</EmptyStateIcon>
            <EmptyStateTitle>No Scraping Logs Yet</EmptyStateTitle>
            <EmptyStateText>
              Start your first scraping job to see logs here. 
              <br />
              Click "Start Scraping" to begin collecting car listings.
            </EmptyStateText>
          </EmptyState>
        ) : (
          <LogsTable>
            <thead>
              <tr>
                <TableHeader style={{ width: '50px' }}>
                  <Checkbox
                    type="checkbox"
                    checked={selectAll}
                    onChange={handleSelectAll}
                  />
                </TableHeader>
                <TableHeader>Site</TableHeader>
                <TableHeader>Started</TableHeader>
                <TableHeader>Completed</TableHeader>
                <TableHeader>Duration</TableHeader>
                <TableHeader>Status</TableHeader>
                <TableHeader>Listings</TableHeader>
                <TableHeader>Pages</TableHeader>
                <TableHeader>Errors</TableHeader>
              </tr>
            </thead>
            <tbody>
              {logs?.logs?.map((log) => (
                <tr key={log.id}>
                  <CheckboxCell>
                    <Checkbox
                      type="checkbox"
                      checked={selectedRows.has(log.id)}
                      onChange={() => handleSelectRow(log.id)}
                    />
                  </CheckboxCell>
                  <TableCell>{log.site_name}</TableCell>
                  <TableCell>{formatDate(log.started_at)}</TableCell>
                  <TableCell>
                    {log.completed_at ? formatDate(log.completed_at) : '-'}
                  </TableCell>
                  <TableCell>
                    {formatDuration(log.started_at, log.completed_at)}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={log.status}>
                      {log.status.toUpperCase()}
                    </StatusBadge>
                    {log.is_blocked && (
                      <span style={{ color: '#e74c3c', marginLeft: '5px' }}>🚫</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {log.listings_found} found
                    {log.listings_new > 0 && (
                      <div style={{ fontSize: '0.8rem', color: '#27ae60' }}>
                        +{log.listings_new} new
                      </div>
                    )}
                    {log.listings_updated > 0 && (
                      <div style={{ fontSize: '0.8rem', color: '#f39c12' }}>
                        {log.listings_updated} updated
                      </div>
                    )}
                    {log.listings_removed > 0 && (
                      <div style={{ fontSize: '0.8rem', color: '#e74c3c' }}>
                        -{log.listings_removed} removed
                      </div>
                    )}
                  </TableCell>
                  <TableCell>{log.pages_scraped}</TableCell>
                  <TableCell>
                    {log.errors && log.errors.length > 0 ? (
                      <span style={{ color: '#e74c3c' }}>
                        {log.errors.length} error(s)
                      </span>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                </tr>
              ))}
            </tbody>
          </LogsTable>
        )}
      </Section>

      {/* Statistics */}
      {stats && (
        <Section>
          <SectionTitle>Scraping Statistics (Last 7 Days)</SectionTitle>
          <StatusCard>
            <StatusItem>
              <StatusValue>{stats.total_scrapes || 0}</StatusValue>
              <StatusLabel>Total Scrapes</StatusLabel>
            </StatusItem>
            
            <StatusItem>
              <StatusValue>{stats.successful_scrapes || 0}</StatusValue>
              <StatusLabel>Successful Scrapes</StatusLabel>
            </StatusItem>
            
            <StatusItem>
              <StatusValue>{stats.success_rate || 0}%</StatusValue>
              <StatusLabel>Success Rate</StatusLabel>
            </StatusItem>
            
            <StatusItem>
              <StatusValue>{stats.total_listings || 0}</StatusValue>
              <StatusLabel>Total Listings</StatusLabel>
            </StatusItem>
            
            <StatusItem>
              <StatusValue>{stats.recent_listings || 0}</StatusValue>
              <StatusLabel>Recent Listings</StatusLabel>
            </StatusItem>
          </StatusCard>
          
          {stats.by_source && Object.keys(stats.by_source).length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <h4 style={{ marginBottom: '0.5rem', color: '#666' }}>Listings by Source:</h4>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                {Object.entries(stats.by_source).map(([source, count]) => (
                  <div key={source} style={{ 
                    background: '#f8f9fa', 
                    padding: '0.5rem 1rem', 
                    borderRadius: '4px',
                    fontSize: '0.9rem'
                  }}>
                    <strong>{source}:</strong> {count}
                  </div>
                ))}
              </div>
            </div>
          )}
        </Section>
      )}

      {/* Recent Activity Summary */}
      {recentLogs.length > 0 && (
        <Section>
          <SectionTitle>Recent Activity Summary</SectionTitle>
          <StatusCard>
            <StatusItem>
              <StatusValue>
                {recentLogs.reduce((total, log) => total + (log.listings_found || 0), 0)}
              </StatusValue>
              <StatusLabel>Total Listings Found</StatusLabel>
            </StatusItem>
            
            <StatusItem>
              <StatusValue>
                {recentLogs.reduce((total, log) => total + (log.listings_new || 0), 0)}
              </StatusValue>
              <StatusLabel>New Listings</StatusLabel>
            </StatusItem>
            
            <StatusItem>
              <StatusValue>
                {recentLogs.reduce((total, log) => total + (log.pages_scraped || 0), 0)}
              </StatusValue>
              <StatusLabel>Pages Scraped</StatusLabel>
            </StatusItem>
            
            <StatusItem>
              <StatusValue>
                {recentLogs.filter(log => log.is_blocked).length}
              </StatusValue>
              <StatusLabel>Blocked Sites</StatusLabel>
            </StatusItem>
          </StatusCard>
        </Section>
      )}
    </Container>
  );
};

export default Scraping;
