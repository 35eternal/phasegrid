#!/usr/bin/env python3
"""Test auto_paper with lower confidence threshold"""

import sys
import os

# Temporarily modify the generate_slips call to use lower confidence
original_generate_slips = None

def mock_generate_slips(*args, **kwargs):
    # Force min_confidence to 0.5 for testing
    kwargs['min_confidence'] = 0.5
    from slips_generator import generate_slips as real_generate_slips
    return real_generate_slips(*args, **kwargs)

# Monkey patch it
import slips_generator
slips_generator.generate_slips = mock_generate_slips

# Now run auto_paper
os.system("python auto_paper.py --dry-run --bypass-guard-rail")
