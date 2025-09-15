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

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${props => props.theme.spacing.xl};
  flex-wrap: wrap;
  gap: ${props => props.theme.spacing.lg};
`;

const Title = styled.h1`
  color: ${props => props.theme.colors.primary};
`;

const SearchContainer = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.md};
  flex-wrap: wrap;
`;

const SearchInput = styled.input`
  padding: ${props => props.theme.spacing.md};
  border: 2px solid ${props => props.theme.colors.lightGray};
  border-radius: ${props => props.theme.borderRadius};
  font-size: 1rem;
  min-width: 250px;
  
  &:focus {
    border-color: ${props => props.theme.colors.secondary};
    outline: none;
  }
`;

const FilterButton = styled.button`
  background: ${props => props.theme.colors.secondary};
  color: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  border: none;
  font-weight: 500;
  cursor: pointer;
  
  &:hover {
    background: #2980b9;
  }
`;

const FiltersContainer = styled.div`
  background: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.lg};
  border-radius: ${props => props.theme.borderRadius};
  box-shadow: ${props => props.theme.boxShadow};
  margin-bottom: ${props => props.theme.spacing.lg};
  display: ${props => props.isOpen ? 'block' : 'none'};
`;

const FiltersGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: ${props => props.theme.spacing.lg};
`;

const FilterGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${props => props.theme.spacing.sm};
`;

const FilterLabel = styled.label`
  font-weight: 500;
  color: ${props => props.theme.colors.dark};
`;

const FilterInput = styled.input`
  padding: ${props => props.theme.spacing.sm};
  border: 2px solid ${props => props.theme.colors.lightGray};
  border-radius: ${props => props.theme.borderRadius};
  
  &:focus {
    border-color: ${props => props.theme.colors.secondary};
    outline: none;
  }
`;

const FilterSelect = styled.select`
  padding: ${props => props.theme.spacing.sm};
  border: 2px solid ${props => props.theme.colors.lightGray};
  border-radius: ${props => props.theme.borderRadius};
  
  &:focus {
    border-color: ${props => props.theme.colors.secondary};
    outline: none;
  }
`;

const ListingsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: ${props => props.theme.spacing.lg};
`;

const ListingCard = styled.div`
  background: ${props => props.theme.colors.white};
  border-radius: ${props => props.theme.borderRadius};
  box-shadow: ${props => props.theme.boxShadow};
  overflow: hidden;
  transition: transform 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
  }
`;

const ListingImage = styled.img`
  width: 100%;
  height: 200px;
  object-fit: cover;
`;

const ListingContent = styled.div`
  padding: ${props => props.theme.spacing.lg};
`;

const ListingTitle = styled.h3`
  color: ${props => props.theme.colors.primary};
  margin-bottom: ${props => props.theme.spacing.sm};
  font-size: 1.1rem;
  line-height: 1.4;
`;

const ListingPrice = styled.div`
  font-size: 1.5rem;
  font-weight: bold;
  color: ${props => props.theme.colors.success};
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const ListingLocation = styled.div`
  color: ${props => props.theme.colors.gray};
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const ListingDetails = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${props => props.theme.spacing.md};
  font-size: 0.9rem;
  color: ${props => props.theme.colors.gray};
`;

const DealScore = styled.div`
  background: ${props => {
    const score = props.score;
    if (score >= 80) return props.theme.colors.success;
    if (score >= 60) return props.theme.colors.warning;
    return props.theme.colors.danger;
  }};
  color: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  font-weight: bold;
  font-size: 0.9rem;
`;

const ViewButton = styled.a`
  display: inline-block;
  background: ${props => props.theme.colors.secondary};
  color: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  text-decoration: none;
  font-weight: 500;
  text-align: center;
  width: 100%;
  
  &:hover {
    background: #2980b9;
    text-decoration: none;
    color: ${props => props.theme.colors.white};
  }
`;

const ListingTag = styled.span`
  display: inline-block;
  padding: ${props => props.theme.spacing.xs} ${props => props.theme.spacing.sm};
  border-radius: ${props => props.theme.borderRadius};
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: ${props => props.theme.spacing.sm};
  background: ${props => {
    switch (props.type) {
      case 'dummy': return '#f39c12';
      case 'real': return '#27ae60';
      default: return '#95a5a6';
    }
  }};
  color: ${props => props.theme.colors.white};
`;

const Pagination = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
  margin-top: ${props => props.theme.spacing.xl};
`;

const PageButton = styled.button`
  background: ${props => props.active ? props.theme.colors.secondary : props.theme.colors.white};
  color: ${props => props.active ? props.theme.colors.white : props.theme.colors.dark};
  border: 2px solid ${props => props.theme.colors.lightGray};
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  cursor: pointer;
  
  &:hover {
    background: ${props => props.active ? '#2980b9' : props.theme.colors.light};
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
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

const Listings = () => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({
    search: '',
    min_price: '',
    max_price: '',
    min_score: '',
    max_score: '',
    make: '',
    location: '',
    fuel_type: '',
    transmission: '',
    year_min: '',
    year_max: '',
    mileage_max: '',
    price_dropped: '',
    is_duplicate: '',
    listing_type: '',
    sort_by: 'deal_score',
    sort_order: 'desc'
  });
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  // Build query parameters
  const queryParams = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value && value !== '') {
      queryParams.append(key, value);
    }
  });
  queryParams.append('page', currentPage);
  queryParams.append('per_page', 20);

  // Fetch listings
  const { data, isLoading, error, refetch } = useQuery(
    ['listings', queryParams.toString()],
    () => axios.get(`/api/listings?${queryParams.toString()}`).then(res => res.data),
    { keepPreviousData: true }
  );

  // Delete dummy listings mutation
  const deleteDummyMutation = useMutation(
    () => axios.post('/api/listings/delete-dummy'),
    {
      onSuccess: (response) => {
        toast.success(`Deleted ${response.data.dummy_listings_deleted} dummy listings!`);
        queryClient.invalidateQueries('listings');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to delete dummy listings');
      },
    }
  );

  // Add dummy listings mutation
  const addDummyMutation = useMutation(
    () => axios.post('/api/listings/add-dummy'),
    {
      onSuccess: (response) => {
        toast.success(`Added ${response.data.listings_created} dummy listings!`);
        queryClient.invalidateQueries('listings');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to add dummy listings');
      },
    }
  );

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handleSearch = () => {
    refetch();
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleDeleteDummy = async () => {
    if (window.confirm('Are you sure you want to delete all dummy/test listings? This action cannot be undone.')) {
      await deleteDummyMutation.mutateAsync();
    }
  };

  const handleAddDummy = async () => {
    if (window.confirm('This will add 15 dummy listings for testing. Continue?')) {
      await addDummyMutation.mutateAsync();
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-IE', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatMileage = (mileage) => {
    if (!mileage) return 'N/A';
    return new Intl.NumberFormat('en-IE').format(mileage) + ' km';
  };

  const getListingType = (sourceSite) => {
    // Dummy listings have source_site of 'sample' or 'lewismotors' (our test data)
    if (sourceSite === 'sample' || sourceSite === 'lewismotors') {
      return 'dummy';
    }
    // Real listings come from actual car websites
    return 'real';
  };

  if (isLoading && !data) {
    return (
      <Container>
        <LoadingSpinner>Loading listings...</LoadingSpinner>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <ErrorMessage>
          Error loading listings. Please try again later.
        </ErrorMessage>
      </Container>
    );
  }

  const listings = data?.listings || [];
  const pagination = data?.pagination || {};

  return (
    <Container>
      <Header>
        <Title>Car Listings</Title>
        <SearchContainer>
          <SearchInput
            type="text"
            placeholder="Search listings..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <FilterButton onClick={() => setShowFilters(!showFilters)}>
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </FilterButton>
          <FilterButton onClick={handleSearch}>
            Search
          </FilterButton>
          <FilterButton 
            onClick={handleDeleteDummy}
            disabled={deleteDummyMutation.isLoading}
            style={{ backgroundColor: '#e74c3c' }}
          >
            {deleteDummyMutation.isLoading ? 'Deleting...' : 'Delete Test Listings'}
          </FilterButton>
          <FilterButton 
            onClick={handleAddDummy}
            disabled={addDummyMutation.isLoading}
            style={{ backgroundColor: '#27ae60' }}
          >
            {addDummyMutation.isLoading ? 'Adding...' : 'Add Dummy Data'}
          </FilterButton>
        </SearchContainer>
      </Header>

      {/* Filters */}
      <FiltersContainer isOpen={showFilters}>
        <FiltersGrid>
          <FilterGroup>
            <FilterLabel>Min Price (€)</FilterLabel>
            <FilterInput
              type="number"
              value={filters.min_price}
              onChange={(e) => handleFilterChange('min_price', e.target.value)}
              placeholder="e.g. 5000"
            />
          </FilterGroup>
          
          <FilterGroup>
            <FilterLabel>Max Price (€)</FilterLabel>
            <FilterInput
              type="number"
              value={filters.max_price}
              onChange={(e) => handleFilterChange('max_price', e.target.value)}
              placeholder="e.g. 15000"
            />
          </FilterGroup>
          
          <FilterGroup>
            <FilterLabel>Min Deal Score</FilterLabel>
            <FilterInput
              type="number"
              value={filters.min_score}
              onChange={(e) => handleFilterChange('min_score', e.target.value)}
              placeholder="e.g. 70"
              min="0"
              max="100"
            />
          </FilterGroup>
          
          <FilterGroup>
            <FilterLabel>Make</FilterLabel>
            <FilterInput
              type="text"
              value={filters.make}
              onChange={(e) => handleFilterChange('make', e.target.value)}
              placeholder="e.g. Toyota"
            />
          </FilterGroup>
          
          <FilterGroup>
            <FilterLabel>Location</FilterLabel>
            <FilterInput
              type="text"
              value={filters.location}
              onChange={(e) => handleFilterChange('location', e.target.value)}
              placeholder="e.g. Dublin"
            />
          </FilterGroup>
          
          <FilterGroup>
            <FilterLabel>Fuel Type</FilterLabel>
            <FilterSelect
              value={filters.fuel_type}
              onChange={(e) => handleFilterChange('fuel_type', e.target.value)}
            >
              <option value="">All</option>
              <option value="Petrol">Petrol</option>
              <option value="Diesel">Diesel</option>
              <option value="Electric">Electric</option>
              <option value="Hybrid">Hybrid</option>
            </FilterSelect>
          </FilterGroup>
          
          <FilterGroup>
            <FilterLabel>Transmission</FilterLabel>
            <FilterSelect
              value={filters.transmission}
              onChange={(e) => handleFilterChange('transmission', e.target.value)}
            >
              <option value="">All</option>
              <option value="Manual">Manual</option>
              <option value="Automatic">Automatic</option>
            </FilterSelect>
          </FilterGroup>
          
          <FilterGroup>
            <FilterLabel>Listing Type</FilterLabel>
            <FilterSelect
              value={filters.listing_type}
              onChange={(e) => handleFilterChange('listing_type', e.target.value)}
            >
              <option value="">All Listings</option>
              <option value="real">Real Listings Only</option>
              <option value="dummy">Dummy Data Only</option>
            </FilterSelect>
          </FilterGroup>
          
          <FilterGroup>
            <FilterLabel>Sort By</FilterLabel>
            <FilterSelect
              value={filters.sort_by}
              onChange={(e) => handleFilterChange('sort_by', e.target.value)}
            >
              <option value="deal_score">Deal Score</option>
              <option value="price">Price</option>
              <option value="year">Year</option>
              <option value="mileage">Mileage</option>
              <option value="created_at">Date Added</option>
            </FilterSelect>
          </FilterGroup>
        </FiltersGrid>
      </FiltersContainer>

      {/* Listings Grid */}
      <ListingsGrid>
        {listings.map((listing) => (
          <ListingCard key={listing.id}>
            {listing.image_url && (
              <ListingImage 
                src={listing.image_url} 
                alt={listing.title}
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            )}
            <ListingContent>
              <ListingTag type={getListingType(listing.source_site)}>
                {getListingType(listing.source_site) === 'dummy' ? 'Dummy Data' : 'Real Listing'}
              </ListingTag>
              <ListingTitle>{listing.title}</ListingTitle>
              <ListingPrice>{formatPrice(listing.price)}</ListingPrice>
              <ListingLocation>📍 {listing.location}</ListingLocation>
              
              <ListingDetails>
                <div>
                  {listing.year && <div>Year: {listing.year}</div>}
                  {listing.mileage && <div>Mileage: {formatMileage(listing.mileage)}</div>}
                  {listing.fuel_type && <div>Fuel: {listing.fuel_type}</div>}
                  {listing.transmission && <div>Transmission: {listing.transmission}</div>}
                </div>
                <DealScore score={listing.deal_score}>
                  {listing.deal_score.toFixed(1)}
                </DealScore>
              </ListingDetails>
              
              {listing.price_dropped && (
                <div style={{ 
                  color: '#27ae60', 
                  fontWeight: 'bold', 
                  marginBottom: '10px',
                  fontSize: '0.9rem'
                }}>
                  🔥 Price Dropped by €{listing.price_drop_amount}
                </div>
              )}
              
              <ViewButton href={listing.url} target="_blank" rel="noopener noreferrer">
                View Listing
              </ViewButton>
            </ListingContent>
          </ListingCard>
        ))}
      </ListingsGrid>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <Pagination>
          <PageButton
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={!pagination.has_prev}
          >
            Previous
          </PageButton>
          
          {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
            const page = i + 1;
            return (
              <PageButton
                key={page}
                active={page === currentPage}
                onClick={() => handlePageChange(page)}
              >
                {page}
              </PageButton>
            );
          })}
          
          <PageButton
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={!pagination.has_next}
          >
            Next
          </PageButton>
        </Pagination>
      )}

      {listings.length === 0 && !isLoading && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#7f8c8d' }}>
          No listings found matching your criteria.
        </div>
      )}
    </Container>
  );
};

export default Listings;
