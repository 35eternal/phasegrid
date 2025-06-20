"""Test Google Sheets connection - requires live credentials."""
import pytest
import os

# Skip if no credentials available
if not os.path.exists('credentials.json'):
    pytest.skip("requires live creds", allow_module_level=True)


class TestLiveConnection:
    """Live API tests - only run with valid credentials."""
    
    def test_sheet_connection(self):
        """Test basic sheet connection."""
        from scripts.repair_sheets import SheetRepair
        repair = SheetRepair()
        assert repair.service is not None
    
    def test_verify_sheets(self):
        """Test sheet verification."""
        from scripts.verify_sheets import SheetVerifier
        verifier = SheetVerifier()
        results = verifier.run_verification()
        assert results is not None