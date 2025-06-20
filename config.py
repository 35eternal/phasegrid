"""
WNBA Predictor Configuration
Centralized configuration for all components
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
MODELS_DIR = PROJECT_ROOT / "models"

# Data paths
PLAYER_MAPPING_FILE = DATA_DIR / "mappings/player_final_mapping.csv"
PROPS_FILE = DATA_DIR / "raw/wnba_prizepicks_props.json"
GAMELOGS_DIR = DATA_DIR / "processed/gamelogs"

# API Configuration
PRIZEPICKS_API = "https://api.prizepicks.com/projections"
BASKETBALL_REF_BASE = "https://www.basketball-reference.com"

# Model parameters
CONFIDENCE_THRESHOLD = 0.75
MIN_EDGE_THRESHOLD = 5.0
ROLLING_GAME_WINDOWS = [3, 5, 7, 10]

# Scraping parameters
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REQUEST_DELAY = 1.0  # seconds between requests

# Output settings
SIGNAL_COLUMNS = [
    'timestamp', 'player', 'prop_type', 'line', 'prediction',
    'edge', 'confidence', 'action', 'recent_avg'
]

# Feature engineering
FEATURES = [
    'games_played', 'minutes_avg', 'stat_avg_3g', 'stat_avg_5g',
    'stat_avg_10g', 'stat_std', 'days_rest', 'home_away',
    'opponent_defensive_rating', 'trend_direction'
]