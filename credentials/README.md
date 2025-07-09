# Credentials Setup

This folder contains credential templates. Actual credentials should NEVER be committed.

## Setup Instructions

1. Copy service_account.example.json to service_account.json
2. Replace placeholder values with your actual service account credentials
3. Ensure service_account.json is listed in .gitignore

## Security Notes

- Never commit actual credentials
- Use environment variables or secret management services in production
- The base64 encoded version in .env is also sensitive
