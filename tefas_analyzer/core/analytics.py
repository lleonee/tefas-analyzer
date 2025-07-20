"""
Financial analytics and metrics calculation for mutual fund analysis.

This module provides comprehensive financial analysis tools including
return calculations, risk metrics, and performance comparisons.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union
import logging

# Logger tanımı (merkezi konfigürasyon api.py'dan gelecek)
logger = logging.getLogger(__name__)

# Constants
TRADING_DAYS_PER_YEAR = 252
MIN_DATA_POINTS = 30  # Minimum data points for reliable calculations


def calculate_total_return(price_series: pd.Series) -> float:
    """
    Calculate total return percentage from price series.
    
    Args:
        price_series (pd.Series): Time series of prices (datetime index required)
        
    Returns:
        float: Total return as percentage (e.g., 25.5 for 25.5%)
        
    Raises:
        ValueError: If price_series is empty, has insufficient data, or contains invalid values
        
    Example:
        >>> prices = pd.Series([100, 110, 125], index=pd.date_range('2023-01-01', periods=3))
        >>> calculate_total_return(prices)
        25.0
    """
    # Input validation
    if not isinstance(price_series, pd.Series):
        raise ValueError("price_series must be a pandas Series")
    
    if len(price_series) < 2:
        raise ValueError("price_series must contain at least 2 data points")
    
    if price_series.isnull().any():
        raise ValueError("price_series contains NaN values")
    
    if (price_series <= 0).any():
        raise ValueError("price_series contains non-positive values")
    
    # Sort by index to ensure chronological order
    price_series = price_series.sort_index()
    
    initial_price = price_series.iloc[0]
    final_price = price_series.iloc[-1]
    
    if initial_price <= 0:
        raise ValueError("Initial price must be positive")
    
    total_return = ((final_price - initial_price) / initial_price) * 100
    
    logger.debug(f"Total return calculated: {total_return:.2f}%")
    return float(total_return)


def calculate_annualized_volatility(price_series: pd.Series) -> float:
    """
    Calculate annualized volatility from price series using daily log returns.
    
    Args:
        price_series (pd.Series): Time series of prices (datetime index required)
        
    Returns:
        float: Annualized volatility as percentage (e.g., 18.5 for 18.5%)
        
    Raises:
        ValueError: If price_series is empty, has insufficient data, or contains invalid values
        
    Example:
        >>> prices = pd.Series([100, 102, 98, 105], index=pd.date_range('2023-01-01', periods=4))
        >>> vol = calculate_annualized_volatility(prices)
        >>> isinstance(vol, float)
        True
    """
    # Input validation
    if not isinstance(price_series, pd.Series):
        raise ValueError("price_series must be a pandas Series")
    
    if len(price_series) < MIN_DATA_POINTS:
        raise ValueError(f"price_series must contain at least {MIN_DATA_POINTS} data points for reliable volatility calculation")
    
    if price_series.isnull().any():
        raise ValueError("price_series contains NaN values")
    
    if (price_series <= 0).any():
        raise ValueError("price_series contains non-positive values")
    
    # Sort by index to ensure chronological order
    price_series = price_series.sort_index()
    
    # Calculate daily log returns
    log_returns = np.log(price_series / price_series.shift(1)).dropna()
    
    if len(log_returns) < 2:
        raise ValueError("Insufficient data for return calculation after processing")
    
    # Calculate daily volatility (standard deviation of log returns)
    daily_volatility = log_returns.std()
    
    if np.isnan(daily_volatility) or np.isinf(daily_volatility):
        raise ValueError("Cannot calculate volatility due to invalid returns")
    
    # Annualize volatility
    annualized_volatility = daily_volatility * np.sqrt(TRADING_DAYS_PER_YEAR) * 100
    
    logger.debug(f"Annualized volatility calculated: {annualized_volatility:.2f}%")
    return float(annualized_volatility)


def calculate_cagr(price_series: pd.Series) -> float:
    """
    Calculate Compound Annual Growth Rate (CAGR) from price series.
    
    Args:
        price_series (pd.Series): Time series of prices (datetime index required)
        
    Returns:
        float: CAGR as percentage (e.g., 12.3 for 12.3% annual growth)
        
    Raises:
        ValueError: If price_series is empty, has insufficient data, or contains invalid values
        
    Example:
        >>> prices = pd.Series([100, 110, 121], index=pd.date_range('2023-01-01', periods=3, freq='Y'))
        >>> cagr = calculate_cagr(prices)
        >>> isinstance(cagr, float)
        True
    """
    # Input validation
    if not isinstance(price_series, pd.Series):
        raise ValueError("price_series must be a pandas Series")
    
    if len(price_series) < 2:
        raise ValueError("price_series must contain at least 2 data points")
    
    if not isinstance(price_series.index, pd.DatetimeIndex):
        raise ValueError("price_series must have a DatetimeIndex")
    
    if price_series.isnull().any():
        raise ValueError("price_series contains NaN values")
    
    if (price_series <= 0).any():
        raise ValueError("price_series contains non-positive values")
    
    # Sort by index to ensure chronological order
    price_series = price_series.sort_index()
    
    initial_price = price_series.iloc[0]
    final_price = price_series.iloc[-1]
    
    # Calculate time period in years
    start_date = price_series.index[0]
    end_date = price_series.index[-1]
    time_period_days = (end_date - start_date).days
    
    if time_period_days <= 0:
        raise ValueError("End date must be after start date")
    
    time_period_years = time_period_days / 365.25  # Account for leap years
    
    if time_period_years < 1/365.25:  # Less than a day
        raise ValueError("Time period is too short for CAGR calculation")
    
    # Calculate CAGR: ((Final/Initial)^(1/years)) - 1
    cagr = (((final_price / initial_price) ** (1 / time_period_years)) - 1) * 100
    
    if np.isnan(cagr) or np.isinf(cagr):
        raise ValueError("Cannot calculate CAGR due to invalid price data")
    
    logger.debug(f"CAGR calculated: {cagr:.2f}% over {time_period_years:.2f} years")
    return float(cagr)


def calculate_sharpe_ratio(price_series: pd.Series, risk_free_rate: float = 0.15) -> float:
    """
    Calculate Sharpe ratio from price series.
    
    Args:
        price_series (pd.Series): Time series of prices (datetime index required)
        risk_free_rate (float): Annual risk-free rate as decimal (default 0.15 for 15%)
        
    Returns:
        float: Sharpe ratio (not as percentage, e.g., 1.25 not 125%)
        
    Raises:
        ValueError: If price_series is empty, has insufficient data, or contains invalid values
        
    Example:
        >>> prices = pd.Series([100, 102, 105, 103], index=pd.date_range('2023-01-01', periods=4))
        >>> sharpe = calculate_sharpe_ratio(prices, risk_free_rate=0.10)
        >>> isinstance(sharpe, float)
        True
    """
    # Input validation
    if not isinstance(price_series, pd.Series):
        raise ValueError("price_series must be a pandas Series")
    
    if len(price_series) < MIN_DATA_POINTS:
        raise ValueError(f"price_series must contain at least {MIN_DATA_POINTS} data points for reliable Sharpe ratio calculation")
    
    if not isinstance(price_series.index, pd.DatetimeIndex):
        raise ValueError("price_series must have a DatetimeIndex")
    
    if price_series.isnull().any():
        raise ValueError("price_series contains NaN values")
    
    if (price_series <= 0).any():
        raise ValueError("price_series contains non-positive values")
    
    if not isinstance(risk_free_rate, (int, float)):
        raise ValueError("risk_free_rate must be a number")
    
    if risk_free_rate < 0 or risk_free_rate > 1:
        raise ValueError("risk_free_rate should be between 0 and 1 (e.g., 0.15 for 15%)")
    
    # Sort by index to ensure chronological order
    price_series = price_series.sort_index()
    
    # Calculate daily log returns
    log_returns = np.log(price_series / price_series.shift(1)).dropna()
    
    if len(log_returns) < 2:
        raise ValueError("Insufficient data for return calculation after processing")
    
    # Calculate annualized return
    total_days = (price_series.index[-1] - price_series.index[0]).days
    if total_days <= 0:
        raise ValueError("Invalid date range")
    
    annualized_return = (np.exp(log_returns.mean() * TRADING_DAYS_PER_YEAR) - 1)
    
    # Calculate annualized volatility (as decimal, not percentage)
    annualized_volatility = log_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    if annualized_volatility == 0:
        raise ValueError("Cannot calculate Sharpe ratio: volatility is zero")
    
    if np.isnan(annualized_return) or np.isnan(annualized_volatility):
        raise ValueError("Cannot calculate Sharpe ratio due to invalid returns or volatility")
    
    # Calculate Sharpe ratio
    excess_return = annualized_return - risk_free_rate
    sharpe_ratio = excess_return / annualized_volatility
    
    if np.isnan(sharpe_ratio) or np.isinf(sharpe_ratio):
        raise ValueError("Cannot calculate Sharpe ratio due to invalid calculations")
    
    logger.debug(f"Sharpe ratio calculated: {sharpe_ratio:.3f} (annualized return: {annualized_return*100:.2f}%, volatility: {annualized_volatility*100:.2f}%)")
    return float(sharpe_ratio)


def calculate_beta(price_series: pd.Series, benchmark_series: pd.Series) -> float:
    """
    Calculate beta coefficient comparing fund returns to benchmark returns.
    
    Args:
        price_series (pd.Series): Time series of fund prices (datetime index required)
        benchmark_series (pd.Series): Time series of benchmark prices (datetime index required)
        
    Returns:
        float: Beta coefficient (not as percentage, e.g., 1.2 not 120%)
        
    Raises:
        ValueError: If series are empty, have insufficient data, or contain invalid values
        
    Example:
        >>> fund_prices = pd.Series([100, 105, 102], index=pd.date_range('2023-01-01', periods=3))
        >>> benchmark_prices = pd.Series([1000, 1020, 1010], index=pd.date_range('2023-01-01', periods=3))
        >>> beta = calculate_beta(fund_prices, benchmark_prices)
        >>> isinstance(beta, float)
        True
    """
    # Input validation
    if not isinstance(price_series, pd.Series) or not isinstance(benchmark_series, pd.Series):
        raise ValueError("Both price_series and benchmark_series must be pandas Series")
    
    if len(price_series) < MIN_DATA_POINTS or len(benchmark_series) < MIN_DATA_POINTS:
        raise ValueError(f"Both series must contain at least {MIN_DATA_POINTS} data points for reliable beta calculation")
    
    if not isinstance(price_series.index, pd.DatetimeIndex) or not isinstance(benchmark_series.index, pd.DatetimeIndex):
        raise ValueError("Both series must have DatetimeIndex")
    
    if price_series.isnull().any() or benchmark_series.isnull().any():
        raise ValueError("Series contain NaN values")
    
    if (price_series <= 0).any() or (benchmark_series <= 0).any():
        raise ValueError("Series contain non-positive values")
    
    # Sort by index to ensure chronological order
    price_series = price_series.sort_index()
    benchmark_series = benchmark_series.sort_index()
    
    # Align the series by their common date range
    common_dates = price_series.index.intersection(benchmark_series.index)
    
    if len(common_dates) < MIN_DATA_POINTS:
        raise ValueError(f"Insufficient overlapping data points: {len(common_dates)} (minimum {MIN_DATA_POINTS} required)")
    
    # Filter to common dates
    aligned_fund = price_series.loc[common_dates]
    aligned_benchmark = benchmark_series.loc[common_dates]
    
    # Calculate daily log returns
    fund_returns = np.log(aligned_fund / aligned_fund.shift(1)).dropna()
    benchmark_returns = np.log(aligned_benchmark / aligned_benchmark.shift(1)).dropna()
    
    # Ensure both return series have the same length
    min_length = min(len(fund_returns), len(benchmark_returns))
    if min_length < 2:
        raise ValueError("Insufficient return data for beta calculation")
    
    fund_returns = fund_returns.iloc[-min_length:]
    benchmark_returns = benchmark_returns.iloc[-min_length:]
    
    # Calculate covariance and benchmark variance
    covariance = np.cov(fund_returns, benchmark_returns)[0, 1]
    benchmark_variance = np.var(benchmark_returns)
    
    if benchmark_variance == 0:
        raise ValueError("Cannot calculate beta: benchmark has zero variance")
    
    if np.isnan(covariance) or np.isnan(benchmark_variance):
        raise ValueError("Cannot calculate beta due to invalid covariance or variance")
    
    # Calculate beta
    beta = covariance / benchmark_variance
    
    if np.isnan(beta) or np.isinf(beta):
        raise ValueError("Cannot calculate beta due to invalid calculations")
    
    logger.debug(f"Beta calculated: {beta:.3f}")
    return float(beta)


def get_fund_statistics(fund_code: str, price_series: pd.Series) -> Dict[str, Any]:
    """
    Calculate comprehensive fund statistics from price series.
    Args:
        fund_code (str): Fund code for identification
        price_series (pd.Series): Series with Date index and price values
    Returns:
        Dict[str, Any]: Dictionary containing all calculated metrics
    Raises:
        ValueError: If Series is empty or has invalid structure
    """
    if price_series.empty:
        raise ValueError("Price series is empty")
    if not isinstance(price_series, pd.Series):
        raise ValueError("Input must be a pandas Series")
    if not pd.api.types.is_datetime64_any_dtype(price_series.index):
        raise ValueError("Index must be datetime")
    # Calculate all metrics
    stats = {
        'Fon_Kodu': fund_code,
        'Ilk_Fiyat': float(price_series.iloc[0]),
        'Son_Fiyat': float(price_series.iloc[-1]),
        'Min_Fiyat': float(price_series.min()),
        'Max_Fiyat': float(price_series.max()),
        'Ortalama_Fiyat': float(price_series.mean()),
        'Veri_Sayisi': len(price_series),
        'Ilk_Tarih': price_series.index[0],
        'Son_Tarih': price_series.index[-1]
    }
    try:
        stats['Toplam_Getiri_%'] = calculate_total_return(price_series)
    except ValueError as e:
        logger.warning(f"Could not calculate total return: {e}")
        stats['Toplam_Getiri_%'] = None
    try:
        stats['Volatilite_%'] = calculate_annualized_volatility(price_series)
    except ValueError as e:
        logger.warning(f"Could not calculate volatility: {e}")
        stats['Volatilite_%'] = None
    try:
        stats['CAGR_%'] = calculate_cagr(price_series)
    except ValueError as e:
        logger.warning(f"Could not calculate CAGR: {e}")
        stats['CAGR_%'] = None
    try:
        stats['Sharpe_Ratio'] = calculate_sharpe_ratio(price_series)
    except ValueError as e:
        logger.warning(f"Could not calculate Sharpe Ratio: {e}")
        stats['Sharpe_Ratio'] = None
    return stats


def calculate_financial_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate advanced financial metrics from price data.
    Args:
        df (pd.DataFrame): DataFrame with Date index and 'Price' column
    Returns:
        Dict[str, float]: Financial metrics
    """
    if df.empty:
        return {}
    if 'Price' not in df.columns:
        raise ValueError("DataFrame must contain column: 'Price'")
    price_series = df['Price']
    price_series.index = pd.to_datetime(df.index)
    metrics = {}
    try:
        metrics['total_return'] = calculate_total_return(price_series)
        metrics['volatility'] = calculate_annualized_volatility(price_series)
        metrics['cagr'] = calculate_cagr(price_series)
        metrics['sharpe_ratio'] = calculate_sharpe_ratio(price_series)
    except ValueError as e:
        logger.warning(f"Error calculating financial metrics: {e}")
    return metrics
