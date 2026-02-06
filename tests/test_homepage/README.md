# Homepage Tests

This directory contains tests for the homepage functionality of the MelonMind application.

## Test Functions

### `test_homepage()`
- Tests the HTML homepage access at root path (`/`)
- Verifies status code 200
- Checks content type is `text/html`
- Validates HTML content includes `<title>MelonMind`

### `test_api_home()`
- Tests the API homepage at `/api/`
- Verifies status code 200
- Checks content type is `application/json`
- Validates JSON response contains `message` field with `MelonMind API`

### `test_health_check()`
- Tests the health check endpoint at `/health/`
- Verifies status code 200
- Checks response contains 'running' text
- Confirms service availability

## Running Tests

Execute the tests with:
```bash
cd /path/to/MelonMind
python tests/test_homepage/test_homepage.py
```