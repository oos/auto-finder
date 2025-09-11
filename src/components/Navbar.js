import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useAuth } from '../contexts/AuthContext';

const Nav = styled.nav`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: ${props => props.theme.colors.white};
  box-shadow: ${props => props.theme.boxShadow};
  z-index: 1000;
  height: 80px;
`;

const NavContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 ${props => props.theme.spacing.lg};
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Logo = styled(Link)`
  font-size: 1.5rem;
  font-weight: bold;
  color: ${props => props.theme.colors.primary};
  text-decoration: none;
  
  &:hover {
    text-decoration: none;
  }
`;

const NavLinks = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.lg};
  
  @media (max-width: ${props => props.theme.breakpoints.mobile}) {
    display: ${props => props.isOpen ? 'flex' : 'none'};
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: ${props => props.theme.colors.white};
    flex-direction: column;
    padding: ${props => props.theme.spacing.lg};
    box-shadow: ${props => props.theme.boxShadow};
  }
`;

const NavLink = styled(Link)`
  color: ${props => props.theme.colors.dark};
  text-decoration: none;
  font-weight: 500;
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  transition: all 0.2s ease;
  
  &:hover {
    background: ${props => props.theme.colors.light};
    text-decoration: none;
  }
  
  &.active {
    background: ${props => props.theme.colors.secondary};
    color: ${props => props.theme.colors.white};
  }
`;

const UserMenu = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
`;

const UserName = styled.span`
  color: ${props => props.theme.colors.dark};
  font-weight: 500;
`;

const LogoutButton = styled.button`
  background: ${props => props.theme.colors.danger};
  color: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  font-weight: 500;
  transition: all 0.2s ease;
  
  &:hover {
    background: #c0392b;
  }
`;

const MobileMenuButton = styled.button`
  display: none;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: ${props => props.theme.colors.dark};
  
  @media (max-width: ${props => props.theme.breakpoints.mobile}) {
    display: block;
  }
`;

const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  if (!user) {
    return null;
  }

  return (
    <Nav>
      <NavContainer>
        <Logo to="/dashboard">🚗 Auto Finder</Logo>
        
        <NavLinks isOpen={isMobileMenuOpen}>
          <NavLink 
            to="/dashboard" 
            className={isActive('/dashboard') ? 'active' : ''}
            onClick={() => setIsMobileMenuOpen(false)}
          >
            Dashboard
          </NavLink>
          <NavLink 
            to="/listings" 
            className={isActive('/listings') ? 'active' : ''}
            onClick={() => setIsMobileMenuOpen(false)}
          >
            Listings
          </NavLink>
          <NavLink 
            to="/scraping" 
            className={isActive('/scraping') ? 'active' : ''}
            onClick={() => setIsMobileMenuOpen(false)}
          >
            Scraping
          </NavLink>
          <NavLink 
            to="/settings" 
            className={isActive('/settings') ? 'active' : ''}
            onClick={() => setIsMobileMenuOpen(false)}
          >
            Settings
          </NavLink>
        </NavLinks>
        
        <UserMenu>
          <UserName>Hello, {user.first_name}</UserName>
          <LogoutButton onClick={handleLogout}>
            Logout
          </LogoutButton>
        </UserMenu>
        
        <MobileMenuButton onClick={toggleMobileMenu}>
          ☰
        </MobileMenuButton>
      </NavContainer>
    </Nav>
  );
};

export default Navbar;
