"""
TEFAS Fund Analyzer - A yfinance-like Python package for Turkish mutual fund analysis.

This package provides a simple, clean API to download, analyze, and visualize 
Turkish mutual fund data from the TEFAS platform.

Usage:
    import tefas_analyzer as tefas
    
    # Download fund data (like yfinance!)
    df = tefas.download('CPU')
    
    # Get statistics  
    stats = tefas.get_statistics(df, 'CPU')
    
    # Plot chart
    tefas.plot_price_chart(df, 'CPU')
    
    # Quick analysis
    result = tefas.analyze('CPU')
"""

__version__ = "1.0.0"
__author__ = "Leone"
__email__ = "leone@example.com"

# Import ONLY the main API functions (clean yfinance-like interface)
from .api import (
    download,           # Main data download function
    get_statistics      # Calculate financial metrics  
)

# CLI entry point
from .cli import main

# Clean public API - only these 6 functions + CLI
__all__ = [
    # Core API functions (yfinance-like)
    "download",
    "get_statistics", 
    "main"
]

# Package metadata
__title__ = "TEFAS Fund Analyzer"
__description__ = "A yfinance-like Python package for Turkish mutual fund analysis"
__url__ = "https://github.com/leone/tefas-analyzer"
__license__ = "MIT"
