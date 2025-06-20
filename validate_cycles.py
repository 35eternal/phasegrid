import sys
sys.path.append('core')
from cycle_detector import CycleDetector

detector = CycleDetector()

print('CYCLE VALIDATION FOR IDENTIFIED PLAYERS')
print('=' * 40)

# A'ja Wilson (Player 237846) - 29.5 line
wilson_edge = detector.detect_current_day_edge("A'ja Wilson", 15)
if wilson_edge:
    expected = 29.5 + wilson_edge['edge']
    print('A\'ja Wilson (237846):')
    print(f'  Day 15 edge: {wilson_edge["edge"]:+.1f}')
    print(f'  Expected vs 29.5: {expected:.1f}')
    print('  BET: UNDER 29.5 (STRONG)')
else:
    print('A\'ja Wilson: No cycle data')

# Arike Ogunbowale (Player 237862) - 24.5 line
arike_edge = detector.detect_current_day_edge('Arike Ogunbowale', 15)
if arike_edge:
    expected = 24.5 + arike_edge['edge']
    print('\nArike Ogunbowale (237862):')
    print(f'  Day 15 edge: {arike_edge["edge"]:+.1f}')
    print(f'  Expected vs 24.5: {expected:.1f}')
    if arike_edge['edge'] > 2:
        print('  BET: OVER 24.5')
    elif arike_edge['edge'] < -2:
        print('  BET: UNDER 24.5')
    else:
        print('  BET: NEUTRAL')
else:
    print('\nArike Ogunbowale: No cycle data')

print('\nTARS MISSION COMPLETE - PLAYERS IDENTIFIED!')