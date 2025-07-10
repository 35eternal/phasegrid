# A6: Night-of Dry-Run & Grader Rehearsal - Evidence

## Important Discovery
Found broken webhook issue - Slack sent email about "invalidated webhook URLs" which explains why alerts aren't working.

## Dry-Run (19:30 UTC)
- **GitHub Actions URL**: https://github.com/35eternal/phasegrid/actions/runs/16183888549
- **Slack Alert**: No alert - webhook is broken (see email evidence)
- **Discord Alert**: No alert generated
- **Google Sheet paper_slips**: Empty - no slips created

## Nightly Grader (21:30 UTC)
- **GitHub Actions URL**: https://github.com/35eternal/phasegrid/actions/runs/16183854964
- **Slack Alert**: No alert - webhook is broken
- **Discord Alert**: Test alerts exist but no grader alert
- **Google Sheet grades**: No data

## Coverage Verification
TOTAL                           521     99  81.00%
Required test coverage of 80% reached. Total coverage: 81.00%

## CI Status
All checks passing on branch: feat/a6-dryrun-grader ✅

## Key Finding
The smoke tests work (using mock webhooks) but production webhooks are broken, preventing real alerts from being sent.