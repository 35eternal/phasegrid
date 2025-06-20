# Coverage Debt - Sprint-3 Snapshot (June 19, 2025)

## Current Status
**Overall Coverage: 12%** (Target: 90%)

## Modules Lacking Tests

| Module | Lines | Covered | % |
|--------|-------|---------|---|
| paper_trader.py | 115 | 0 | 0% |
| slip_optimizer.py | 211 | 44 | 21% |
| bankroll_optimizer.py | 132 | 28 | 21% |
| sheet_connector.py | 114 | 17 | 15% |
| scripts/repair_sheets.py | 117 | 74 | 63% |
| modules/sheet_connector.py | 115 | 43 | 37% |
| core/prediction_engine.py | 231 | 161 | 70% |
| **TOTAL** | 12,788 | 1,473 | **12%** |

## Technical Debt Notes
- 27 legacy tests marked as xfail (need updating to new interfaces)
- Critical modules (paper_trader, optimizers) have minimal coverage
- Integration tests missing for Google Sheets operations

## Sprint Goals
- **Sprint-4**: Target ≥60% coverage
  - Add unit tests for paper_trader.py
  - Complete tests for slip_optimizer.py
  - Fix xfail tests in test_bankroll_optimizer.py
  
- **Sprint-5**: Target ≥90% coverage  
  - Add integration tests
  - End-to-end workflow tests
  - Mock Google Sheets API calls
