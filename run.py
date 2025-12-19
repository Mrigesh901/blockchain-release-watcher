#!/usr/bin/env python3
"""
Entry point script for running the blockchain release monitor.
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import main

if __name__ == "__main__":
    main()
