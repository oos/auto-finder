import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import styled from 'styled-components';
import axios from 'axios';
import toast from 'react-hot-toast';

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

const InfoBox = styled.div`
  background: #e7f3ff;
  color: #0066cc;
  padding: ${props => props.theme.spacing.lg};
  border-radius: ${props => props.theme.borderRadius};
  border: 1px solid #b3d9ff;
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const Scraping = () => {
  const queryClient = useQueryClient();
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);

  // Fetch scraping status
  const { data: status, isLoading: statusLoading, error: statusError } = useQuery(
    'scraping-status',
    () => axios.get('/api/scraping/status').then(res => res.data),
    { refetchInterval: 5000 } // Refetch every 5 seconds
  );

  // Fetch scraping logs
  const { data: logs, isLoading: logsLoading, error: logsError } = useQuery(
    'scraping-logs',
    () => axios.get('/api/scraping/logs?per_page=50').then(res => res.data)
  );

  // Start scraping mutation
  const startScrapingMutation = useMutation(
    () => axios.post('/api/scraping/start'),
    {
      onSuccess: () => {
        toast.success('Scraping started successfully!');
        queryClient.invalidateQueries('scraping-status');
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
        <strong>How it works:</strong> The scraping system automatically collects car listings from multiple Irish websites. 
        It runs daily and processes listings to detect duplicates, calculate deal scores, and send email notifications. 
        You can manually start/stop scraping and monitor the progress here.
      </InfoBox>

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
        ) : (
          <LogsTable>
            <thead>
              <tr>
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
      {recentLogs.length > 0 && (
        <Section>
          <SectionTitle>Last 24 Hours Summary</SectionTitle>
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
