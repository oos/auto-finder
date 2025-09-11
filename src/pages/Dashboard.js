import React from 'react';
import { useQuery } from 'react-query';
import styled from 'styled-components';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: ${props => props.theme.spacing.lg};
`;

const Header = styled.div`
  margin-bottom: ${props => props.theme.spacing.xl};
`;

const Title = styled.h1`
  color: ${props => props.theme.colors.primary};
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const Subtitle = styled.p`
  color: ${props => props.theme.colors.gray};
  font-size: 1.1rem;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: ${props => props.theme.spacing.lg};
  margin-bottom: ${props => props.theme.spacing.xl};
`;

const StatCard = styled.div`
  background: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.lg};
  border-radius: ${props => props.theme.borderRadius};
  box-shadow: ${props => props.theme.boxShadow};
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: bold;
  color: ${props => props.theme.colors.primary};
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const StatLabel = styled.div`
  color: ${props => props.theme.colors.gray};
  font-weight: 500;
`;

const ChartsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: ${props => props.theme.spacing.lg};
  margin-bottom: ${props => props.theme.spacing.xl};
`;

const ChartCard = styled.div`
  background: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.lg};
  border-radius: ${props => props.theme.borderRadius};
  box-shadow: ${props => props.theme.boxShadow};
`;

const ChartTitle = styled.h3`
  color: ${props => props.theme.colors.primary};
  margin-bottom: ${props => props.theme.spacing.lg};
  text-align: center;
`;

const AlertsSection = styled.div`
  background: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.lg};
  border-radius: ${props => props.theme.borderRadius};
  box-shadow: ${props => props.theme.boxShadow};
  margin-bottom: ${props => props.theme.spacing.xl};
`;

const AlertItem = styled.div`
  padding: ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  margin-bottom: ${props => props.theme.spacing.md};
  border-left: 4px solid ${props => {
    switch (props.priority) {
      case 'high': return props.theme.colors.danger;
      case 'medium': return props.theme.colors.warning;
      default: return props.theme.colors.gray;
    }
  }};
  background: ${props => {
    switch (props.priority) {
      case 'high': return '#fee';
      case 'medium': return '#fff3cd';
      default: return '#f8f9fa';
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

const Dashboard = () => {
  // Fetch dashboard data
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useQuery(
    'dashboard-overview',
    () => axios.get('/api/dashboard/overview').then(res => res.data),
    { refetchInterval: 30000 } // Refetch every 30 seconds
  );

  const { data: trends, isLoading: trendsLoading } = useQuery(
    'dashboard-trends',
    () => axios.get('/api/dashboard/charts/trends?days=30').then(res => res.data)
  );

  const { data: distribution, isLoading: distributionLoading } = useQuery(
    'dashboard-distribution',
    () => axios.get('/api/dashboard/charts/distribution').then(res => res.data)
  );

  const { data: alerts, isLoading: alertsLoading } = useQuery(
    'dashboard-alerts',
    () => axios.get('/api/dashboard/alerts').then(res => res.data)
  );

  if (overviewLoading) {
    return (
      <Container>
        <LoadingSpinner>Loading dashboard...</LoadingSpinner>
      </Container>
    );
  }

  if (overviewError) {
    return (
      <Container>
        <ErrorMessage>
          Error loading dashboard data. Please try again later.
        </ErrorMessage>
      </Container>
    );
  }

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <Container>
      <Header>
        <Title>Dashboard</Title>
        <Subtitle>Your used car deal tracking overview</Subtitle>
      </Header>

      {/* Overview Stats */}
      <StatsGrid>
        <StatCard>
          <StatValue>{overview?.overview?.total_listings || 0}</StatValue>
          <StatLabel>Total Listings</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{overview?.overview?.active_listings || 0}</StatValue>
          <StatLabel>Active Listings</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{overview?.overview?.recent_listings || 0}</StatValue>
          <StatLabel>New This Week</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{overview?.overview?.price_drops || 0}</StatValue>
          <StatLabel>Price Drops</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{overview?.overview?.top_deals || 0}</StatValue>
          <StatLabel>Top Deals (80+ Score)</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{overview?.overview?.avg_deal_score?.toFixed(1) || 0}</StatValue>
          <StatLabel>Avg Deal Score</StatLabel>
        </StatCard>
      </StatsGrid>

      {/* Charts */}
      <ChartsGrid>
        <ChartCard>
          <ChartTitle>Daily Listings Trend</ChartTitle>
          {trendsLoading ? (
            <LoadingSpinner>Loading chart...</LoadingSpinner>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends?.daily_listings || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#3498db" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard>
          <ChartTitle>Average Deal Score Trend</ChartTitle>
          {trendsLoading ? (
            <LoadingSpinner>Loading chart...</LoadingSpinner>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends?.daily_scores || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="avg_score" stroke="#27ae60" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard>
          <ChartTitle>Listings by Source Site</ChartTitle>
          {distributionLoading ? (
            <LoadingSpinner>Loading chart...</LoadingSpinner>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={distribution?.by_site || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="site" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3498db" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard>
          <ChartTitle>Listings by Make</ChartTitle>
          {distributionLoading ? (
            <LoadingSpinner>Loading chart...</LoadingSpinner>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={distribution?.by_make?.slice(0, 5) || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ make, count }) => `${make}: ${count}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {(distribution?.by_make?.slice(0, 5) || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </ChartsGrid>

      {/* Alerts */}
      <AlertsSection>
        <ChartTitle>Recent Alerts</ChartTitle>
        {alertsLoading ? (
          <LoadingSpinner>Loading alerts...</LoadingSpinner>
        ) : alerts?.alerts?.length > 0 ? (
          alerts.alerts.map((alert, index) => (
            <AlertItem key={index} priority={alert.priority}>
              <strong>{alert.type.replace('_', ' ').toUpperCase()}:</strong> {alert.message}
            </AlertItem>
          ))
        ) : (
          <p style={{ textAlign: 'center', color: '#7f8c8d' }}>No recent alerts</p>
        )}
      </AlertsSection>
    </Container>
  );
};

export default Dashboard;
