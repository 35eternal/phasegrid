# PhaseGrid

![Tests](https://github.com/35eternal/phasegrid/actions/workflows/tests.yml/badge.svg)

A phase-based betting system with Kelly criterion optimization.

## Overview

PhaseGrid is a sports betting system that uses phase-based analysis and Kelly criterion calculations to optimize betting strategies. The system integrates with Google Sheets for data management and provides automated betting recommendations.

## Features

- Phase-based betting analysis
- Kelly criterion stake optimization  
- Google Sheets integration
- Automated paper trading
- Performance tracking and reporting
- CI/CD with GitHub Actions

## Project Structure

    phasegrid/
    ├── modules/          # Core betting logic and utilities
    ├── scripts/          # Executable scripts and tools
    ├── tests/           # Test suite
    ├── config/          # Configuration files
    ├── docs/            # Documentation
    ├── output/          # Generated output files
    └── .github/         # GitHub Actions workflows

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions including Google Sheets configuration.

## Testing

Run tests with:

    pytest

Run tests with coverage:

    pytest --cov=modules --cov=scripts

## Coverage

Current test coverage: 12% - See [Coverage Debt Documentation](docs/coverage_debt.md) for improvement plan.

## Configuration

1. Copy `.env.example` to `.env`
2. Update the values in `.env` with your settings
3. See [QUICKSTART.md](QUICKSTART.md) for Google Sheets setup

## Scripts

- `paper_trader.py` - Run paper trading simulations
- `verify_sheets.py` - Verify Google Sheets connection
- `repair_sheets.py` - Repair sheet data issues
- `update_results.py` - Update betting results

## License

Private repository - All rights reserved