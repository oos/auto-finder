import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useAuth } from '../contexts/AuthContext';

const Container = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: ${props => props.theme.spacing.lg};
`;

const Card = styled.div`
  background: ${props => props.theme.colors.white};
  border-radius: ${props => props.theme.borderRadius};
  box-shadow: ${props => props.theme.boxShadow};
  padding: ${props => props.theme.spacing.xxl};
  width: 100%;
  max-width: 400px;
`;

const Title = styled.h1`
  text-align: center;
  margin-bottom: ${props => props.theme.spacing.xl};
  color: ${props => props.theme.colors.primary};
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
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
  transition: border-color 0.2s ease;
  
  &:focus {
    border-color: ${props => props.theme.colors.secondary};
  }
  
  &.error {
    border-color: ${props => props.theme.colors.danger};
  }
`;

const Button = styled.button`
  background: ${props => props.theme.colors.secondary};
  color: ${props => props.theme.colors.white};
  padding: ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s ease;
  
  &:hover {
    background: #2980b9;
  }
  
  &:disabled {
    background: ${props => props.theme.colors.lightGray};
    cursor: not-allowed;
  }
`;

const LinkText = styled.p`
  text-align: center;
  margin-top: ${props => props.theme.spacing.lg};
  color: ${props => props.theme.colors.gray};
`;

const ErrorMessage = styled.div`
  background: #fee;
  color: ${props => props.theme.colors.danger};
  padding: ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  border: 1px solid #fcc;
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      const result = await login(formData.email, formData.password);
      if (result.success) {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Login error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container>
      <Card>
        <Title>Login</Title>
        
        <Form onSubmit={handleSubmit}>
          <FormGroup>
            <Label htmlFor="email">Email</Label>
            <Input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={errors.email ? 'error' : ''}
              placeholder="Enter your email"
            />
            {errors.email && <ErrorMessage>{errors.email}</ErrorMessage>}
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="password">Password</Label>
            <Input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={errors.password ? 'error' : ''}
              placeholder="Enter your password"
            />
            {errors.password && <ErrorMessage>{errors.password}</ErrorMessage>}
          </FormGroup>
          
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Logging in...' : 'Login'}
          </Button>
        </Form>
        
        <LinkText>
          Don't have an account? <Link to="/register">Register here</Link>
        </LinkText>
      </Card>
    </Container>
  );
};

export default Login;
