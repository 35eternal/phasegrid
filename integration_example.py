"""
PG-109: Example of how to integrate cycle tracking into slip_optimizer.py
This shows the minimal changes needed to add cycle awareness
"""

# Add these imports to slip_optimizer.py:
# from phasegrid.cycle_tracker import CycleTracker
# from pathlib import Path
# import json

# Add this method to the SlipOptimizer class:
def apply_cycle_modifier_example():
    """
    Example method to add to SlipOptimizer class
    """
    code = '''
    def apply_cycle_modifiers(self, player_name, prop_type, base_projection, player_id=None):
        """Apply cycle phase modifiers to player projections"""
        # Initialize cycle tracker if not already done
        if not hasattr(self, 'cycle_tracker'):
            self.cycle_tracker = CycleTracker()
            self.cycle_tracker.load_from_file()
            
            # Load config
            config_path = Path("config/cycle_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.cycle_config = json.load(f)
            else:
                self.cycle_config = None
        
        # Return unchanged if no config or tracking disabled
        if not self.cycle_config or not self.cycle_config.get('cycle_tracking', {}).get('enabled', False):
            return base_projection
        
        # If no player_id provided, return base projection
        if not player_id:
            return base_projection
        
        # Get the phase modifier
        from datetime import date
        modifier = self.cycle_tracker.get_phase_modifier(player_id, date.today())
        
        # Apply prop-specific modifier if available
        if self.cycle_config.get('cycle_tracking', {}).get('use_prop_specific_modifiers', False):
            # Get player's current phase
            player_entries = self.cycle_tracker.cycle_data.get(str(player_id), [])
            if player_entries:
                latest_entry = max(player_entries, key=lambda x: x.date)
                if (date.today() - latest_entry.date).days <= 35:
                    phase = latest_entry.cycle_phase
                    prop_mods = self.cycle_config['phase_modifiers'][phase]['prop_modifiers']
                    prop_key = prop_type.replace(' ', '').lower()
                    if prop_key in prop_mods:
                        modifier = prop_mods[prop_key]
        
        return base_projection * modifier
    '''
    return code

# Example usage in optimize_slips method:
def integrate_in_optimize_slips():
    """
    Example of how to modify the optimize_slips method
    """
    integration_point = '''
    # In optimize_slips method, when processing each player's projection:
    
    # Original code:
    # projection_value = float(projection['projection'])
    
    # Modified code with cycle tracking:
    player_id = self.get_player_id_mapping(player_name)  # You'll need to implement this mapping
    projection_value = float(projection['projection'])
    projection_value = self.apply_cycle_modifiers(
        player_name, 
        prop_type, 
        projection_value, 
        player_id
    )
    '''
    return integration_point

print("Integration Example for slip_optimizer.py")
print("="*60)
print("\n1. Add this method to SlipOptimizer class:")
print(apply_cycle_modifier_example())
print("\n2. Modify optimize_slips method:")
print(integrate_in_optimize_slips())
print("\n3. Create a player ID mapping system to link player names to anonymous IDs")
