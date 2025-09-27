# Testing Guide

This guide covers all aspects of testing the Source2Social application, from unit tests to integration testing and end-to-end testing.

## Table of Contents
- [Testing Strategy](#testing-strategy)
- [Test Environment Setup](#test-environment-setup)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [API Testing](#api-testing)
- [Webhook Testing](#webhook-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Performance Testing](#performance-testing)
- [Test Data Management](#test-data-management)
- [Continuous Integration](#continuous-integration)

## Testing Strategy

Source2Social uses a comprehensive testing approach covering multiple layers:

### Testing Pyramid
```
        /\
       /  \
      / E2E \     ← End-to-End Tests (Few)
     /______\
    /        \
   /Integration\ ← Integration Tests (Some)
  /____________\
 /              \
/   Unit Tests   \ ← Unit Tests (Many)
/________________\
```

### Test Types
1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test HTTP endpoints and responses
4. **Webhook Tests**: Test GitHub webhook processing
5. **E2E Tests**: Test complete user workflows
6. **Performance Tests**: Test system performance and load

## Test Environment Setup

### 1. Install Testing Dependencies

```bash
pip install pytest pytest-cov pytest-mock requests-mock
```

### 2. Create Test Configuration

Create `tests/conftest.py`:

```python
import pytest
import os
import tempfile
from app import app, init_db

@pytest.fixture
def client():
    """Create test client with temporary database."""
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

@pytest.fixture
def sample_webhook_payload():
    """Sample GitHub webhook payload for testing."""
    return {
        "ref": "refs/heads/main",
        "commits": [
            {
                "id": "abc123",
                "message": "feat: add user authentication",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com"
                },
                "added": ["src/auth.py"],
                "modified": ["README.md"],
                "removed": []
            }
        ],
        "repository": {
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "html_url": "https://github.com/testuser/test-repo"
        }
    }
```

### 3. Environment Variables for Testing

Create `tests/.env.test`:

```bash
# Test Configuration
TESTING=True
DATABASE_PATH=:memory:
GITHUB_WEBHOOK_SECRET=test-secret
TWITTER_API_KEY=test-key
TWITTER_API_SECRET=test-secret
OPENAI_API_KEY=test-key
CODERABBIT_API_KEY=test-key
```

## Unit Testing

### 1. Test Database Operations

Create `tests/test_database.py`:

```python
import pytest
from database.db import create_post, get_posts_by_status, init_db

class TestDatabase:
    def test_create_post(self, client):
        """Test post creation."""
        post_data = {
            'commit_hash': 'abc123',
            'commit_message': 'Test commit',
            'author': 'Test User',
            'repository': 'test-repo',
            'generated_content': 'Test post content'
        }
        
        post_id = create_post(post_data)
        assert post_id is not None
        
        posts = get_posts_by_status('draft')
        assert len(posts) == 1
        assert posts[0]['commit_message'] == 'Test commit'
    
    def test_get_posts_by_status(self, client):
        """Test filtering posts by status."""
        # Create test posts with different statuses
        post_data = {
            'commit_hash': 'abc123',
            'commit_message': 'Test commit',
            'author': 'Test User',
            'repository': 'test-repo',
            'generated_content': 'Test post content',
            'status': 'draft'
        }
        create_post(post_data)
        
        post_data['status'] = 'published'
        post_data['commit_hash'] = 'def456'
        create_post(post_data)
        
        draft_posts = get_posts_by_status('draft')
        published_posts = get_posts_by_status('published')
        
        assert len(draft_posts) == 1
        assert len(published_posts) == 1
```

### 2. Test Post Generation Logic

Create `tests/test_post_generation.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from app import generate_post_from_commit

class TestPostGeneration:
    def test_generate_post_from_commit(self, sample_webhook_payload):
        """Test post generation from commit data."""
        commit = sample_webhook_payload['commits'][0]
        
        with patch('app.openai_client') as mock_openai:
            mock_openai.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="🚀 Just shipped: add user authentication\n\nAdded new authentication system with secure login.\n\n#coding #buildinpublic"))]
            )
            
            result = generate_post_from_commit(commit)
            
            assert result is not None
            assert 'add user authentication' in result
            assert '#coding' in result
    
    def test_apply_post_template(self):
        """Test post template application."""
        content = "Test content"
        template = "🚀 {content} #buildinpublic"
        
        result = apply_post_template(content, template)
        expected = "🚀 Test content #buildinpublic"
        
        assert result == expected
```

### 3. Test Utility Functions

Create `tests/test_utils.py`:

```python
import pytest
from app import validate_webhook_signature, extract_commit_data

class TestUtils:
    def test_validate_webhook_signature(self):
        """Test webhook signature validation."""
        payload = '{"test": "data"}'
        secret = 'test-secret'
        signature = 'sha256=test-signature'
        
        # This would need proper HMAC implementation
        # For now, test the function exists and handles errors
        try:
            result = validate_webhook_signature(payload, signature, secret)
            assert isinstance(result, bool)
        except NotImplementedError:
            pytest.skip("Webhook validation not implemented")
    
    def test_extract_commit_data(self, sample_webhook_payload):
        """Test commit data extraction."""
        commits = extract_commit_data(sample_webhook_payload)
        
        assert len(commits) == 1
        assert commits[0]['id'] == 'abc123'
        assert commits[0]['message'] == 'feat: add user authentication'
        assert commits[0]['author']['name'] == 'Test User'
```

## Integration Testing

### 1. Test GitHub Integration

Create `tests/test_github_integration.py`:

```python
import pytest
import requests_mock
from app import process_github_webhook

class TestGitHubIntegration:
    def test_process_github_webhook(self, client, sample_webhook_payload):
        """Test complete GitHub webhook processing."""
        with requests_mock.Mocker() as m:
            # Mock external API calls
            m.post('https://api.openai.com/v1/chat/completions', 
                   json={'choices': [{'message': {'content': 'Test post'}}]})
            
            response = client.post('/webhook/github', 
                                 json=sample_webhook_payload,
                                 headers={'X-Hub-Signature-256': 'sha256=test'})
            
            assert response.status_code == 200
            
            # Verify post was created
            posts = get_posts_by_status('draft')
            assert len(posts) == 1
```

### 2. Test Social Media Integration

Create `tests/test_social_media.py`:

```python
import pytest
import requests_mock
from app import publish_to_twitter

class TestSocialMediaIntegration:
    def test_publish_to_twitter(self):
        """Test Twitter posting functionality."""
        post_content = "Test post content"
        
        with requests_mock.Mocker() as m:
            m.post('https://api.twitter.com/2/tweets', 
                   json={'data': {'id': '123456789'}})
            
            result = publish_to_twitter(post_content)
            
            assert result is not None
            assert result['id'] == '123456789'
    
    def test_twitter_oauth_flow(self, client):
        """Test Twitter OAuth flow."""
        with requests_mock.Mocker() as m:
            m.post('https://api.twitter.com/oauth/request_token',
                   text='oauth_token=test_token&oauth_token_secret=test_secret')
            
            response = client.get('/integrations/twitter/auth')
            
            assert response.status_code == 302  # Redirect
```

## API Testing

### 1. Test API Endpoints

Create `tests/test_api.py`:

```python
import pytest
import json

class TestAPI:
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
    
    def test_dashboard_endpoint(self, client):
        """Test dashboard endpoint."""
        response = client.get('/dashboard')
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_posts_endpoint(self, client):
        """Test posts listing endpoint."""
        # Create test post first
        post_data = {
            'commit_hash': 'abc123',
            'commit_message': 'Test commit',
            'author': 'Test User',
            'repository': 'test-repo',
            'generated_content': 'Test post content'
        }
        create_post(post_data)
        
        response = client.get('/posts')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['posts']) == 1
    
    def test_post_creation_endpoint(self, client):
        """Test post creation via API."""
        post_data = {
            'commit_hash': 'abc123',
            'commit_message': 'Test commit',
            'author': 'Test User',
            'repository': 'test-repo',
            'generated_content': 'Test post content'
        }
        
        response = client.post('/posts', json=post_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['status'] == 'success'
```

### 2. Test Error Handling

Create `tests/test_error_handling.py`:

```python
import pytest

class TestErrorHandling:
    def test_invalid_webhook_signature(self, client, sample_webhook_payload):
        """Test invalid webhook signature handling."""
        response = client.post('/webhook/github',
                             json=sample_webhook_payload,
                             headers={'X-Hub-Signature-256': 'invalid-signature'})
        
        assert response.status_code == 401
    
    def test_missing_required_fields(self, client):
        """Test missing required fields handling."""
        incomplete_data = {
            'commit_message': 'Test commit'
            # Missing required fields
        }
        
        response = client.post('/posts', json=incomplete_data)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_database_error_handling(self, client):
        """Test database error handling."""
        # This would test database connection failures
        # Implementation depends on your error handling strategy
        pass
```

## Webhook Testing

### 1. Test Webhook Processing

Create `tests/test_webhook.py`:

```python
import pytest
import hmac
import hashlib
import json

class TestWebhook:
    def test_webhook_signature_validation(self):
        """Test webhook signature validation."""
        payload = '{"test": "data"}'
        secret = 'test-secret'
        
        # Generate valid signature
        signature = 'sha256=' + hmac.new(
            secret.encode(), 
            payload.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        result = validate_webhook_signature(payload, signature, secret)
        assert result is True
    
    def test_webhook_payload_processing(self, client, sample_webhook_payload):
        """Test webhook payload processing."""
        # Generate valid signature
        payload = json.dumps(sample_webhook_payload)
        secret = 'test-secret'
        signature = 'sha256=' + hmac.new(
            secret.encode(), 
            payload.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        response = client.post('/webhook/github',
                             data=payload,
                             headers={
                                 'Content-Type': 'application/json',
                                 'X-Hub-Signature-256': signature
                             })
        
        assert response.status_code == 200
    
    def test_webhook_with_multiple_commits(self, client):
        """Test webhook with multiple commits."""
        payload = {
            "ref": "refs/heads/main",
            "commits": [
                {
                    "id": "abc123",
                    "message": "feat: add feature A",
                    "author": {"name": "User 1"},
                    "added": ["feature_a.py"],
                    "modified": [],
                    "removed": []
                },
                {
                    "id": "def456",
                    "message": "fix: fix bug B",
                    "author": {"name": "User 2"},
                    "added": [],
                    "modified": ["bug_fix.py"],
                    "removed": []
                }
            ],
            "repository": {
                "name": "test-repo",
                "full_name": "testuser/test-repo"
            }
        }
        
        # Process webhook and verify multiple posts created
        # Implementation depends on your webhook processing logic
        pass
```

## End-to-End Testing

### 1. Test Complete User Workflows

Create `tests/test_e2e.py`:

```python
import pytest
import time

class TestE2E:
    def test_complete_commit_to_post_workflow(self, client):
        """Test complete workflow from commit to published post."""
        # 1. Simulate GitHub webhook
        webhook_payload = {
            "ref": "refs/heads/main",
            "commits": [{
                "id": "abc123",
                "message": "feat: add amazing feature",
                "author": {"name": "Test User"},
                "added": ["amazing_feature.py"],
                "modified": [],
                "removed": []
            }],
            "repository": {
                "name": "test-repo",
                "full_name": "testuser/test-repo"
            }
        }
        
        # 2. Send webhook
        response = client.post('/webhook/github', json=webhook_payload)
        assert response.status_code == 200
        
        # 3. Check post was created
        posts_response = client.get('/posts')
        posts_data = json.loads(posts_response.data)
        assert len(posts_data['posts']) == 1
        
        post_id = posts_data['posts'][0]['id']
        
        # 4. Edit post
        edit_data = {
            'generated_content': '🚀 Just shipped: add amazing feature\n\nThis feature will revolutionize everything!\n\n#coding #buildinpublic'
        }
        
        edit_response = client.put(f'/posts/{post_id}', json=edit_data)
        assert edit_response.status_code == 200
        
        # 5. Publish post
        publish_response = client.post(f'/posts/{post_id}/publish')
        assert publish_response.status_code == 200
        
        # 6. Verify post status
        posts_response = client.get('/posts')
        posts_data = json.loads(posts_response.data)
        assert posts_data['posts'][0]['status'] == 'published'
    
    def test_dashboard_navigation(self, client):
        """Test dashboard navigation and functionality."""
        # 1. Access dashboard
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        # 2. Navigate to settings
        response = client.get('/settings')
        assert response.status_code == 200
        
        # 3. Navigate to integrations
        response = client.get('/integrations')
        assert response.status_code == 200
```

## Performance Testing

### 1. Load Testing

Create `tests/test_performance.py`:

```python
import pytest
import time
import concurrent.futures

class TestPerformance:
    def test_webhook_processing_performance(self, client, sample_webhook_payload):
        """Test webhook processing performance."""
        start_time = time.time()
        
        # Process multiple webhooks concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    client.post, 
                    '/webhook/github', 
                    json=sample_webhook_payload
                ) for _ in range(50)
            ]
            
            results = [future.result() for future in futures]
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
        
        # Processing should be reasonably fast
        assert processing_time < 10  # seconds
    
    def test_database_query_performance(self, client):
        """Test database query performance."""
        # Create many posts
        for i in range(100):
            post_data = {
                'commit_hash': f'hash{i}',
                'commit_message': f'Test commit {i}',
                'author': 'Test User',
                'repository': 'test-repo',
                'generated_content': f'Test content {i}'
            }
            create_post(post_data)
        
        # Test query performance
        start_time = time.time()
        posts = get_posts_by_status('draft')
        end_time = time.time()
        
        query_time = end_time - start_time
        assert len(posts) == 100
        assert query_time < 1  # seconds
```

## Test Data Management

### 1. Test Data Fixtures

Create `tests/fixtures.py`:

```python
import pytest
import json

@pytest.fixture
def sample_commits():
    """Sample commit data for testing."""
    return [
        {
            "id": "abc123",
            "message": "feat: add user authentication",
            "author": {"name": "Developer 1", "email": "dev1@example.com"},
            "added": ["src/auth.py", "src/login.py"],
            "modified": ["README.md"],
            "removed": []
        },
        {
            "id": "def456",
            "message": "fix: resolve memory leak",
            "author": {"name": "Developer 2", "email": "dev2@example.com"},
            "added": [],
            "modified": ["src/processor.py"],
            "removed": []
        }
    ]

@pytest.fixture
def sample_repository():
    """Sample repository data for testing."""
    return {
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "html_url": "https://github.com/testuser/test-repo",
        "description": "A test repository",
        "language": "Python"
    }

@pytest.fixture
def sample_generated_posts():
    """Sample generated posts for testing."""
    return [
        "🚀 Just shipped: add user authentication\n\nAdded secure login system with JWT tokens.\n\n#coding #buildinpublic",
        "🐛 Fixed: resolve memory leak\n\nOptimized data processing to prevent memory issues.\n\n#coding #bugfix"
    ]
```

### 2. Test Data Cleanup

```python
@pytest.fixture(autouse=True)
def cleanup_test_data(client):
    """Automatically cleanup test data after each test."""
    yield
    # Cleanup logic here
    pass
```

## Continuous Integration

### 1. GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=app --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 2. Test Commands

Add to `Makefile`:

```makefile
.PHONY: test test-unit test-integration test-e2e test-coverage

test:
	pytest tests/

test-unit:
	pytest tests/test_*.py -k "not integration and not e2e"

test-integration:
	pytest tests/test_*integration*.py

test-e2e:
	pytest tests/test_e2e.py

test-coverage:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

test-watch:
	pytest-watch tests/
```

## Running Tests

### 1. Run All Tests
```bash
pytest tests/
```

### 2. Run Specific Test Types
```bash
# Unit tests only
pytest tests/test_*.py -k "not integration and not e2e"

# Integration tests only
pytest tests/test_*integration*.py

# End-to-end tests only
pytest tests/test_e2e.py
```

### 3. Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

### 4. Run Specific Test File
```bash
pytest tests/test_database.py
```

### 5. Run Specific Test Function
```bash
pytest tests/test_database.py::TestDatabase::test_create_post
```

## Best Practices

### 1. Test Organization
- Group related tests in classes
- Use descriptive test names
- Keep tests independent and isolated
- Use fixtures for common setup

### 2. Test Data
- Use realistic test data
- Avoid hardcoded values
- Clean up test data after tests
- Use factories for complex objects

### 3. Assertions
- Use specific assertions
- Test both success and failure cases
- Verify side effects
- Check error messages

### 4. Mocking
- Mock external dependencies
- Use `requests_mock` for HTTP calls
- Mock time-dependent functions
- Verify mock calls when important

### 5. Performance
- Set reasonable timeouts
- Test with realistic data volumes
- Monitor test execution time
- Use parallel execution when possible

---

This testing guide provides a comprehensive framework for ensuring the quality and reliability of the Source2Social application.
