# PhaseGrid Pipeline

Production-ready pipeline for automated sports data processing, featuring daily dry-runs, nightly grading, and PrizePicks integration.

## ?? Features

- **Daily Dry-Run Analysis**: Automated paper trading simulation (`auto_paper.py`)
- **Nightly Result Grading**: Comprehensive grading system (`result_grader.py`)
- **PrizePicks Scraper**: Real-time data collection from PrizePicks API
- **Backfill Capability**: Historical data processing (`backfill.py`)
- **Production Hardened**: Enterprise-ready with proper authentication, error handling, and monitoring

## ?? Prerequisites

- Python 3.8+
- Google Cloud Service Account (for Sheets API access)
- Results API credentials
- Docker (optional, for containerized deployment)

## ?? Installation

### 1. Clone the repository:

    git clone https://github.com/35eternal/phasegrid.git
    cd phasegrid

### 2. Install dependencies:

    pip install -r requirements.txt

### 3. Set up environment variables:

    cp config/production/production.env.example config/production/production.env
    # Edit config/production/production.env with your values

## ?? Authentication Setup

### Google Sheets Authentication

The pipeline now uses file-based service account authentication for Google Sheets API access:

1. Create a service account in Google Cloud Console
2. Download the JSON credentials file
3. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable:

**Windows PowerShell:**

    $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\service-account.json"

**Linux/Mac:**

    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

**Note**: The previous base64-encoded credentials approach has been deprecated due to padding issues.

### Results API Authentication

Configure the Results API endpoint and key:

**Windows PowerShell:**

    $env:RESULTS_API_URL = "https://api.phasegrid.com/v1/"
    $env:RESULTS_API_KEY = "your-api-key-here"

**Linux/Mac:**

    export RESULTS_API_URL=https://api.phasegrid.com/v1/
    export RESULTS_API_KEY=your-api-key-here

## ?? Running the Pipeline

### Daily Dry-Run

    python auto_paper.py

### Nightly Grader

    python scripts/result_grader.py

### Backfill Historical Data

    python backfill.py --start-date 2024-01-01 --end-date 2024-01-31

### Run All Tests

    pytest -v --cov=. --cov-report=term-missing

## ?? Testing

The test suite includes comprehensive unit tests with mocked external dependencies:

### Run specific test modules

    pytest tests/test_sheets_auth.py -v
    pytest tests/test_results_api.py -v

### Run with coverage report

    pytest --cov=. --cov-report=html --cov-report=term-missing

### Coverage threshold enforcement (=80%)

    pytest --cov=. --cov-fail-under=80

## ?? Production Deployment

### Docker Deployment

Build the image:

    docker build -t phasegrid:latest .

Run with production config:

    docker run -d \
      --name phasegrid \
      -v /path/to/credentials:/app/config \
      -e GOOGLE_APPLICATION_CREDENTIALS=/app/config/sheets-service-account.json \
      -e RESULTS_API_KEY=your-api-key \
      -e SENTRY_DSN=your-sentry-dsn \
      phasegrid:latest

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| GOOGLE_APPLICATION_CREDENTIALS | Path to Google service account JSON | ? |
| RESULTS_API_URL | Results API endpoint URL | ? |
| RESULTS_API_KEY | Results API authentication key | ? |
| LOG_LEVEL | Logging level (DEBUG, INFO, WARNING, ERROR) | ? |
| SENTRY_DSN | Sentry error tracking DSN | ? |
| ENVIRONMENT | Deployment environment (production, staging) | ? |

## ?? Monitoring

- **Health Check Endpoint**: http://localhost:8080/health
- **Metrics Endpoint**: http://localhost:9090/metrics
- **Logs**: JSON-formatted logs written to /var/log/phasegrid/app.log

## ??? Production Hardening Features

- ? **Secure Authentication**: File-based Google credentials, API key authentication
- ? **Error Handling**: Comprehensive exception handling with retries
- ? **Connection Pooling**: Optimized HTTP connections with retry logic
- ? **Input Validation**: Strict validation of all API inputs
- ? **Test Coverage**: >80% test coverage with mocked dependencies
- ? **Logging**: Structured JSON logging for production monitoring
- ? **Rate Limiting**: Built-in rate limiting for external API calls
- ? **Batch Processing**: Efficient batch operations for large datasets

## ?? API Integration

### Results API Client

The production-ready Results API client includes:

- Automatic retry logic with exponential backoff
- Connection pooling for efficiency
- Comprehensive error handling
- Batch submission support
- Health check endpoint

### Example usage:

    from api_clients.results_api import get_results_api_client

    client = get_results_api_client()

    # Submit results
    results = [
        {'player_id': 'p1', 'game_date': '2024-01-01', 'score': 100, 'grade': 'A'},
        {'player_id': 'p2', 'game_date': '2024-01-01', 'score': 85, 'grade': 'B'}
    ]
    response = client.submit_results(results)

    # Batch submit for large datasets
    all_results = [...]  # Large list
    responses = client.batch_submit(all_results, batch_size=100)

## ?? Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

## ?? License

This project is licensed under the MIT License - see the LICENSE file for details.

## ?? Support

For issues and questions:
- Create an issue in the GitHub repository
- Contact the development team at dev@phasegrid.com

---

**Production Status**: ? All systems operational

Last updated: 2025-06-24