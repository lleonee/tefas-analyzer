"""
Main API module for TEFAS Fund Analyzer.

This module provides a yfinance-like interface for Turkish mutual fund analysis.
It serves as the single entry point for all fund data operations, analytics, 
and visualization.

Usage Example:
    import tefas_analyzer.api as tefas
    
    # Download fund data
    df = tefas.download('CPU')
    
    # Get additional data
    additional = tefas.get_additional_data('CPU')
    
    # Calculate statistics
    stats = tefas.get_statistics(df)
    
    # Plot charts
    tefas.plot_price_chart(df)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union
import logging

from .core.scraper import get_tefas_data, get_fund_additional_data
from .core.analytics import get_fund_statistics, calculate_financial_metrics
from .utils import clean_fund_code, validate_fund_code, TefasError, ScrapingError

# Configure logging - Kullanıcı verbose parametresi vermezse sessiz çalış
logger = logging.getLogger(__name__)


def download(fund_code: str, headless: bool = True, verbose: bool = False, start: Optional[Union[str, pd.Timestamp]] = None, end: Optional[Union[str, pd.Timestamp]] = None) -> pd.DataFrame:
    """
    Download fund price data from TEFAS (yfinance-like interface).
    Returns a clean pandas DataFrame with datetime index and a single 'Price' column.
    """
    from .utils import setup_logging
    setup_logging(verbose=verbose)
    try:
        if not fund_code or not isinstance(fund_code, str):
            raise ValueError("Fund code must be a non-empty string")
        fund_code = clean_fund_code(fund_code)
        if not validate_fund_code(fund_code):
            raise ValueError(f"Invalid fund code format: {fund_code}")
        logger.info(f"🎯 Downloading data for fund: {fund_code}")
        df = get_tefas_data(fund_code, headless=headless)
        if df.empty:
            raise ScrapingError(f"No data found for fund: {fund_code}")
        if 'Tarih' not in df.columns or 'Fiyat' not in df.columns:
            raise ScrapingError("Downloaded data has unexpected column structure")
        df['Tarih'] = pd.to_datetime(df['Tarih'])
        df['Price'] = pd.to_numeric(df['Fiyat'], errors='coerce')
        df = df.dropna(subset=['Price'])
        df = df.sort_values('Tarih')
        if start is not None:
            start_dt = pd.to_datetime(start)
            df = df[df['Tarih'] >= start_dt]
        if end is not None:
            end_dt = pd.to_datetime(end)
            df = df[df['Tarih'] <= end_dt]
        df = df.set_index('Tarih')
        df.index.name = 'Date'
        df = df[['Price']]
        logger.info(f"✅ Successfully downloaded {len(df)} records for {fund_code}")
        return df
    except (ScrapingError, TefasError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error downloading {fund_code}: {e}")
        raise ScrapingError(f"Failed to download data for {fund_code}: {str(e)}")


def get_statistics(price_df: pd.DataFrame, fund_code: str = "UNKNOWN", benchmark_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Calculate comprehensive financial statistics for a fund.
    Args:
        price_df (pd.DataFrame): DataFrame with Date index and 'Price' column
        fund_code (str): Fund code for identification
        benchmark_df (Optional[pd.DataFrame]): Benchmark data for comparison (not implemented yet)
    Returns:
        Dict[str, Any]: Dictionary containing financial metrics
    """
    try:
        if not isinstance(price_df, pd.DataFrame):
            raise ValueError("price_df must be a pandas DataFrame")
        if price_df.empty:
            raise ValueError("price_df cannot be empty")
        if 'Price' not in price_df.columns:
            raise ValueError("price_df must contain column: 'Price'")
        price_series = price_df['Price']
        price_series.index = pd.to_datetime(price_df.index)
        stats = get_fund_statistics(fund_code, price_series)
        if benchmark_df is not None:
            logger.warning("Benchmark comparison not yet implemented")
            stats['benchmark_comparison'] = None
        logger.info(f"✅ Successfully calculated statistics for {fund_code}")
        return stats
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise ValueError(f"Failed to calculate statistics: {str(e)}")


# Module version info
__version__ = "1.0.0"
__author__ = "TEFAS Analyzer Team"

# Export main functions for easy import
__all__ = [
    'download',
    'get_statistics',
]
