import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import styled from 'styled-components';
import axios from 'axios';
import toast from 'react-hot-toast';

const Container = styled.div`
  max-width: 800px;
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

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.lg};
`;

const FormRow = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: ${props => props.theme.spacing.lg};
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.sm};
`;

const Label = styled.label`
  font-weight: 500;
  color: ${props => props.theme.colors.dark};
`;

const Input = styled.input`
  padding: ${props => props.theme.spacing.md};
  border: 2px solid ${props => props.theme.colors.lightGray};
  border-radius: ${props => props.theme.borderRadius};
  font-size: 1rem;
  
  &:focus {
    border-color: ${props => props.theme.colors.secondary};
    outline: none;
  }
`;

const Select = styled.select`
  padding: ${props => props.theme.spacing.md};
  border: 2px solid ${props => props.theme.colors.lightGray};
  border-radius: ${props => props.theme.borderRadius};
  font-size: 1rem;
  
  &:focus {
    border-color: ${props => props.theme.colors.secondary};
    outline: none;
  }
`;

const CheckboxGroup = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: ${props => props.theme.spacing.md};
`;

const CheckboxItem = styled.label`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  cursor: pointer;
`;

const Checkbox = styled.input`
  width: 18px;
  height: 18px;
`;

const WeightSlider = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
`;

const Slider = styled.input`
  flex: 1;
`;

const SliderValue = styled.span`
  min-width: 30px;
  text-align: center;
  font-weight: bold;
`;

const Button = styled.button`
  background: ${props => props.theme.colors.secondary};
  color: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.md} ${props => props.theme.spacing.lg};
  border-radius: ${props => props.theme.borderRadius};
  border: none;
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

const BlacklistContainer = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.md};
  margin-bottom: ${props => props.theme.spacing.md};
`;

const BlacklistInput = styled.input`
  flex: 1;
  padding: ${props => props.theme.spacing.md};
  border: 2px solid ${props => props.theme.colors.lightGray};
  border-radius: ${props => props.theme.borderRadius};
  
  &:focus {
    border-color: ${props => props.theme.colors.secondary};
    outline: none;
  }
`;

const BlacklistItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.light};
  border-radius: ${props => props.theme.borderRadius};
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const DeleteButton = styled.button`
  background: ${props => props.theme.colors.danger};
  color: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.sm};
  border-radius: ${props => props.theme.borderRadius};
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  
  &:hover {
    background: #c0392b;
  }
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

const Settings = () => {
  const queryClient = useQueryClient();
  const [settings, setSettings] = useState({});
  const [blacklist, setBlacklist] = useState([]);
  const [newBlacklistItem, setNewBlacklistItem] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Fetch settings and blacklist
  const { data, isLoading: dataLoading, error } = useQuery(
    'settings',
    () => axios.get('/api/settings').then(res => res.data)
  );

  // Update settings mutation
  const updateSettingsMutation = useMutation(
    (newSettings) => axios.put('/api/settings', newSettings),
    {
      onSuccess: () => {
        toast.success('Settings updated successfully!');
        queryClient.invalidateQueries('settings');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to update settings');
      },
    }
  );

  // Add blacklist item mutation
  const addBlacklistMutation = useMutation(
    (keyword) => axios.post('/api/settings/blacklist', { keyword }),
    {
      onSuccess: () => {
        toast.success('Keyword added to blacklist');
        queryClient.invalidateQueries('settings');
        setNewBlacklistItem('');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to add keyword');
      },
    }
  );

  // Remove blacklist item mutation
  const removeBlacklistMutation = useMutation(
    (itemId) => axios.delete(`/api/settings/blacklist/${itemId}`),
    {
      onSuccess: () => {
        toast.success('Keyword removed from blacklist');
        queryClient.invalidateQueries('settings');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to remove keyword');
      },
    }
  );

  // Reset weights mutation
  const resetWeightsMutation = useMutation(
    () => axios.post('/api/settings/reset-weights'),
    {
      onSuccess: () => {
        toast.success('Weights reset to default values');
        queryClient.invalidateQueries('settings');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to reset weights');
      },
    }
  );

  useEffect(() => {
    if (data) {
      setSettings(data.settings || {});
      setBlacklist(data.blacklist || []);
    }
  }, [data]);

  const handleSettingsChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleWeightChange = (key, value) => {
    const newValue = parseInt(value);
    setSettings(prev => ({
      ...prev,
      [key]: newValue
    }));
  };

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await updateSettingsMutation.mutateAsync(settings);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddBlacklistItem = async (e) => {
    e.preventDefault();
    if (!newBlacklistItem.trim()) return;
    
    await addBlacklistMutation.mutateAsync(newBlacklistItem.trim().toLowerCase());
  };

  const handleRemoveBlacklistItem = async (itemId) => {
    await removeBlacklistMutation.mutateAsync(itemId);
  };

  const handleResetWeights = async () => {
    await resetWeightsMutation.mutateAsync();
  };

  const calculateTotalWeight = () => {
    const weights = [
      'weight_price_vs_market',
      'weight_mileage_vs_year',
      'weight_co2_tax_band',
      'weight_popularity_rarity',
      'weight_price_dropped',
      'weight_location_match',
      'weight_listing_freshness'
    ];
    
    return weights.reduce((total, weight) => total + (settings[weight] || 0), 0);
  };

  if (dataLoading) {
    return (
      <Container>
        <LoadingSpinner>Loading settings...</LoadingSpinner>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <ErrorMessage>
          Error loading settings. Please try again later.
        </ErrorMessage>
      </Container>
    );
  }

  const totalWeight = calculateTotalWeight();

  return (
    <Container>
      <Title>Settings</Title>

      {/* Price Range Settings */}
      <Section>
        <SectionTitle>Price Range</SectionTitle>
        <Form onSubmit={handleSaveSettings}>
          <FormRow>
            <FormGroup>
              <Label htmlFor="min_price">Minimum Price (€)</Label>
              <Input
                type="number"
                id="min_price"
                value={settings.min_price || ''}
                onChange={(e) => handleSettingsChange('min_price', parseInt(e.target.value))}
                min="0"
              />
            </FormGroup>
            <FormGroup>
              <Label htmlFor="max_price">Maximum Price (€)</Label>
              <Input
                type="number"
                id="max_price"
                value={settings.max_price || ''}
                onChange={(e) => handleSettingsChange('max_price', parseInt(e.target.value))}
                min="0"
              />
            </FormGroup>
          </FormRow>
        </Form>
      </Section>

      {/* Location Settings */}
      <Section>
        <SectionTitle>Location Filter</SectionTitle>
        <Form onSubmit={handleSaveSettings}>
          <FormGroup>
            <Label>Approved Locations (one per line)</Label>
            <textarea
              value={(settings.approved_locations || []).join('\n')}
              onChange={(e) => handleSettingsChange('approved_locations', e.target.value.split('\n').filter(loc => loc.trim()))}
              rows={3}
              style={{
                padding: '12px',
                border: '2px solid #bdc3c7',
                borderRadius: '8px',
                fontSize: '1rem',
                fontFamily: 'inherit'
              }}
              placeholder="Leinster&#10;Dublin&#10;Cork"
            />
          </FormGroup>
        </Form>
      </Section>

      {/* Scraping Settings */}
      <Section>
        <SectionTitle>Scraping Settings</SectionTitle>
        <Form onSubmit={handleSaveSettings}>
          <FormRow>
            <FormGroup>
              <Label htmlFor="max_pages_per_site">Max Pages per Site</Label>
              <Input
                type="number"
                id="max_pages_per_site"
                value={settings.max_pages_per_site || ''}
                onChange={(e) => handleSettingsChange('max_pages_per_site', parseInt(e.target.value))}
                min="1"
                max="50"
              />
            </FormGroup>
            <FormGroup>
              <Label htmlFor="min_deal_score">Minimum Deal Score</Label>
              <Input
                type="number"
                id="min_deal_score"
                value={settings.min_deal_score || ''}
                onChange={(e) => handleSettingsChange('min_deal_score', parseInt(e.target.value))}
                min="0"
                max="100"
              />
            </FormGroup>
          </FormRow>
          
          <FormGroup>
            <Label>Enabled Sites</Label>
            <CheckboxGroup>
              <CheckboxItem>
                <Checkbox
                  type="checkbox"
                  checked={settings.scrape_carzone || false}
                  onChange={(e) => handleSettingsChange('scrape_carzone', e.target.checked)}
                />
                <span>Carzone.ie</span>
              </CheckboxItem>
              <CheckboxItem>
                <Checkbox
                  type="checkbox"
                  checked={settings.scrape_donedeal || false}
                  onChange={(e) => handleSettingsChange('scrape_donedeal', e.target.checked)}
                />
                <span>DoneDeal.ie</span>
              </CheckboxItem>
              <CheckboxItem>
                <Checkbox
                  type="checkbox"
                  checked={settings.scrape_adverts || false}
                  onChange={(e) => handleSettingsChange('scrape_adverts', e.target.checked)}
                />
                <span>Adverts.ie</span>
              </CheckboxItem>
              <CheckboxItem>
                <Checkbox
                  type="checkbox"
                  checked={settings.scrape_carsireland || false}
                  onChange={(e) => handleSettingsChange('scrape_carsireland', e.target.checked)}
                />
                <span>CarsIreland.ie</span>
              </CheckboxItem>
              <CheckboxItem>
                <Checkbox
                  type="checkbox"
                  checked={settings.scrape_lewismotors || false}
                  onChange={(e) => handleSettingsChange('scrape_lewismotors', e.target.checked)}
                />
                <span>LewisMotors.ie</span>
              </CheckboxItem>
            </CheckboxGroup>
          </FormGroup>
        </Form>
      </Section>

      {/* Deal Scoring Weights */}
      <Section>
        <SectionTitle>
          Deal Scoring Weights 
          <span style={{ 
            color: totalWeight === 100 ? '#27ae60' : '#e74c3c',
            marginLeft: '10px',
            fontSize: '0.9rem'
          }}>
            (Total: {totalWeight}/100)
          </span>
        </SectionTitle>
        <Form onSubmit={handleSaveSettings}>
          <FormGroup>
            <WeightSlider>
              <Label htmlFor="weight_price_vs_market">Price vs Market Value</Label>
              <Slider
                type="range"
                id="weight_price_vs_market"
                min="0"
                max="50"
                value={settings.weight_price_vs_market || 25}
                onChange={(e) => handleWeightChange('weight_price_vs_market', e.target.value)}
              />
              <SliderValue>{settings.weight_price_vs_market || 25}</SliderValue>
            </WeightSlider>
          </FormGroup>
          
          <FormGroup>
            <WeightSlider>
              <Label htmlFor="weight_mileage_vs_year">Mileage vs Year</Label>
              <Slider
                type="range"
                id="weight_mileage_vs_year"
                min="0"
                max="50"
                value={settings.weight_mileage_vs_year || 20}
                onChange={(e) => handleWeightChange('weight_mileage_vs_year', e.target.value)}
              />
              <SliderValue>{settings.weight_mileage_vs_year || 20}</SliderValue>
            </WeightSlider>
          </FormGroup>
          
          <FormGroup>
            <WeightSlider>
              <Label htmlFor="weight_co2_tax_band">CO2/Tax Band</Label>
              <Slider
                type="range"
                id="weight_co2_tax_band"
                min="0"
                max="50"
                value={settings.weight_co2_tax_band || 15}
                onChange={(e) => handleWeightChange('weight_co2_tax_band', e.target.value)}
              />
              <SliderValue>{settings.weight_co2_tax_band || 15}</SliderValue>
            </WeightSlider>
          </FormGroup>
          
          <FormGroup>
            <WeightSlider>
              <Label htmlFor="weight_popularity_rarity">Popularity/Rarity</Label>
              <Slider
                type="range"
                id="weight_popularity_rarity"
                min="0"
                max="50"
                value={settings.weight_popularity_rarity || 15}
                onChange={(e) => handleWeightChange('weight_popularity_rarity', e.target.value)}
              />
              <SliderValue>{settings.weight_popularity_rarity || 15}</SliderValue>
            </WeightSlider>
          </FormGroup>
          
          <FormGroup>
            <WeightSlider>
              <Label htmlFor="weight_price_dropped">Price Dropped</Label>
              <Slider
                type="range"
                id="weight_price_dropped"
                min="0"
                max="50"
                value={settings.weight_price_dropped || 10}
                onChange={(e) => handleWeightChange('weight_price_dropped', e.target.value)}
              />
              <SliderValue>{settings.weight_price_dropped || 10}</SliderValue>
            </WeightSlider>
          </FormGroup>
          
          <FormGroup>
            <WeightSlider>
              <Label htmlFor="weight_location_match">Location Match</Label>
              <Slider
                type="range"
                id="weight_location_match"
                min="0"
                max="50"
                value={settings.weight_location_match || 10}
                onChange={(e) => handleWeightChange('weight_location_match', e.target.value)}
              />
              <SliderValue>{settings.weight_location_match || 10}</SliderValue>
            </WeightSlider>
          </FormGroup>
          
          <FormGroup>
            <WeightSlider>
              <Label htmlFor="weight_listing_freshness">Listing Freshness</Label>
              <Slider
                type="range"
                id="weight_listing_freshness"
                min="0"
                max="50"
                value={settings.weight_listing_freshness || 5}
                onChange={(e) => handleWeightChange('weight_listing_freshness', e.target.value)}
              />
              <SliderValue>{settings.weight_listing_freshness || 5}</SliderValue>
            </WeightSlider>
          </FormGroup>
          
          <div style={{ display: 'flex', gap: '10px' }}>
            <Button type="button" onClick={handleResetWeights}>
              Reset to Default
            </Button>
          </div>
        </Form>
      </Section>

      {/* Email Settings */}
      <Section>
        <SectionTitle>Email Notifications</SectionTitle>
        <Form onSubmit={handleSaveSettings}>
          <FormGroup>
            <CheckboxItem>
              <Checkbox
                type="checkbox"
                checked={settings.email_notifications || false}
                onChange={(e) => handleSettingsChange('email_notifications', e.target.checked)}
              />
              <span>Enable daily email notifications</span>
            </CheckboxItem>
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="daily_email_time">Daily Email Time</Label>
            <Input
              type="time"
              id="daily_email_time"
              value={settings.daily_email_time || '09:00'}
              onChange={(e) => handleSettingsChange('daily_email_time', e.target.value)}
            />
          </FormGroup>
        </Form>
      </Section>

      {/* Port Configuration */}
      <Section>
        <SectionTitle>Port Configuration</SectionTitle>
        <Form onSubmit={handleSaveSettings}>
          <FormRow>
            <FormGroup>
              <Label htmlFor="frontend_port">Frontend Port</Label>
              <Input
                type="number"
                id="frontend_port"
                min="1024"
                max="65535"
                value={settings.frontend_port || 3000}
                onChange={(e) => handleSettingsChange('frontend_port', parseInt(e.target.value))}
                placeholder="3000"
              />
              <small>Port for React development server (default: 3000)</small>
            </FormGroup>
            
            <FormGroup>
              <Label htmlFor="backend_port">Backend Port</Label>
              <Input
                type="number"
                id="backend_port"
                min="1024"
                max="65535"
                value={settings.backend_port || 5003}
                onChange={(e) => handleSettingsChange('backend_port', parseInt(e.target.value))}
                placeholder="5003"
              />
              <small>Port for Flask API server (default: 5003)</small>
            </FormGroup>
          </FormRow>
          
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Port Settings'}
            </Button>
          </div>
        </Form>
      </Section>

      {/* Blacklist */}
      <Section>
        <SectionTitle>Blacklisted Keywords</SectionTitle>
        <form onSubmit={handleAddBlacklistItem}>
          <BlacklistContainer>
            <BlacklistInput
              type="text"
              placeholder="Enter keyword to blacklist (e.g., 'write-off', 'accident')"
              value={newBlacklistItem}
              onChange={(e) => setNewBlacklistItem(e.target.value)}
            />
            <Button type="submit">Add</Button>
          </BlacklistContainer>
        </form>
        
        {blacklist.map((item) => (
          <BlacklistItem key={item.id}>
            <span>{item.keyword}</span>
            <DeleteButton onClick={() => handleRemoveBlacklistItem(item.id)}>
              Remove
            </DeleteButton>
          </BlacklistItem>
        ))}
      </Section>

      {/* Save Button */}
      <Section>
        <Button 
          onClick={handleSaveSettings} 
          disabled={isLoading || totalWeight !== 100}
          style={{ 
            width: '100%',
            opacity: totalWeight !== 100 ? 0.5 : 1
          }}
        >
          {isLoading ? 'Saving...' : 'Save All Settings'}
        </Button>
        {totalWeight !== 100 && (
          <p style={{ 
            color: '#e74c3c', 
            textAlign: 'center', 
            marginTop: '10px',
            fontSize: '0.9rem'
          }}>
            Deal scoring weights must total exactly 100 to save settings.
          </p>
        )}
      </Section>
    </Container>
  );
};

export default Settings;
