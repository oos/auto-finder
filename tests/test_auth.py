import pytest
import json
from app import app, db
from models import User

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

@pytest.fixture
def test_user():
    """Create test user"""
    user = User(
        email='test@example.com',
        first_name='Test',
        last_name='User'
    )
    user.set_password('testpassword')
    return user

def test_user_registration(client):
    """Test user registration"""
    response = client.post('/api/auth/register', 
        data=json.dumps({
            'email': 'newuser@example.com',
            'password': 'testpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'token' in data
    assert 'user' in data
    assert data['user']['email'] == 'newuser@example.com'

def test_user_registration_duplicate_email(client, test_user):
    """Test registration with duplicate email"""
    db.session.add(test_user)
    db.session.commit()
    
    response = client.post('/api/auth/register',
        data=json.dumps({
            'email': 'test@example.com',
            'password': 'testpassword123',
            'first_name': 'Another',
            'last_name': 'User'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 409
    data = json.loads(response.data)
    assert 'error' in data

def test_user_login(client, test_user):
    """Test user login"""
    db.session.add(test_user)
    db.session.commit()
    
    response = client.post('/api/auth/login',
        data=json.dumps({
            'email': 'test@example.com',
            'password': 'testpassword'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    assert 'user' in data

def test_user_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials"""
    db.session.add(test_user)
    db.session.commit()
    
    response = client.post('/api/auth/login',
        data=json.dumps({
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data

def test_user_profile(client, test_user):
    """Test getting user profile"""
    db.session.add(test_user)
    db.session.commit()
    
    # Login first
    login_response = client.post('/api/auth/login',
        data=json.dumps({
            'email': 'test@example.com',
            'password': 'testpassword'
        }),
        content_type='application/json'
    )
    
    token = json.loads(login_response.data)['token']
    
    # Get profile
    response = client.get('/api/auth/profile',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user' in data
    assert data['user']['email'] == 'test@example.com'
