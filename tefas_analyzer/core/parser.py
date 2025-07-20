"""
HTML and JavaScript parsing utilities for TEFAS data extraction.

This module contains functions to parse chart data from TEFAS HTML pages
and extract structured data from JavaScript variables.
"""

import re
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging

# Logger tanımı (merkezi konfigürasyon api.py'dan gelecek)
logger = logging.getLogger(__name__)


def parse_chart_data(html: str, fund_code: str) -> pd.DataFrame:
    """
    Parse chart data from TEFAS HTML using working approach.
    
    Args:
        html (str): HTML content from TEFAS page
        fund_code (str): Fund code for identification
        
    Returns:
        pd.DataFrame: DataFrame with 'Tarih' and 'Fiyat' columns
        
    Raises:
        ValueError: If chart data cannot be parsed
    """
    try:
        # Grafik verisini bul - farklı pattern'leri dene
        patterns = [
            r'"data":\[([\d.,\s]+)\]',
            r'data:\[([\d.,\s]+)\]',
            r'"data":\s*\[([\d.,\s]+)\]'
        ]
        
        series_match = None
        for pattern in patterns:
            series_match = re.search(pattern, html)
            if series_match:
                break
        
        # Kategori (tarih) verilerini bul
        xaxis_patterns = [
            r'"categories":\[(.*?)\]',
            r'categories:\[(.*?)\]',
            r'"categories":\s*\[(.*?)\]'
        ]
        
        xaxis_match = None
        for pattern in xaxis_patterns:
            xaxis_match = re.search(pattern, html, re.DOTALL)
            if xaxis_match:
                break

        if not (series_match and xaxis_match):
            raise ValueError(f"Chart data not found for {fund_code}")

        # Fiyat verilerini al
        prices_str = series_match.group(1)
        prices = [float(x.strip()) for x in prices_str.split(',')]
        
        # Tarih verilerini al
        dates_str = xaxis_match.group(1)
        dates = [date.strip().strip('"') for date in dates_str.split(',')]

        if len(prices) != len(dates):
            raise ValueError(f"Price and date data count mismatch: {len(prices)} vs {len(dates)}")

        # DataFrame oluştur
        df = pd.DataFrame({"Tarih": pd.to_datetime(dates, dayfirst=True), "Fiyat": prices})
        df = df.sort_values("Tarih").reset_index(drop=True)
        
        # Sıfır değerleri temizle
        logger.info(f"🔄 Total data count: {len(df)}")
        
        # Sıfır olan değerleri filtrele
        df_filtered = df[df["Fiyat"] != 0].copy()
        
        # Sıfırdan büyük olan ilk değerden başlat
        df_clean = df_filtered[df_filtered["Fiyat"] > 0].copy()
        df_clean = df_clean.reset_index(drop=True)
        
        if len(df_clean) == 0:
            raise ValueError("No valid price data found (all values are zero or negative)")
        
        sifir_sayisi = len(df) - len(df_clean)
        if sifir_sayisi > 0:
            logger.info(f"🧹 Cleaned {sifir_sayisi} zero/negative values.")
        
        logger.info(f"✅ {fund_code} fund: {len(df_clean)} clean records prepared.")
        logger.info(f"📅 Date range: {df_clean['Tarih'].min().strftime('%d.%m.%Y')} - {df_clean['Tarih'].max().strftime('%d.%m.%Y')}")
        logger.info(f"💰 Price range: {df_clean['Fiyat'].min():.4f} - {df_clean['Fiyat'].max():.4f} TL")
        
        return df_clean
        
    except Exception as e:
        logger.error(f"Error parsing chart data for {fund_code}: {e}")
        raise ValueError(f"Failed to parse chart data: {e}")
        if 'series' not in chart_data or len(chart_data['series']) == 0:
            raise ValueError("Series data not found in chart data")
        
        if 'data' not in chart_data['series'][0]:
            raise ValueError("Price data not found in series")
        
        prices_raw = chart_data['series'][0]['data']
        
        # Validate data length consistency
        if len(dates_raw) != len(prices_raw):
            raise ValueError(f"Data length mismatch: {len(dates_raw)} dates vs {len(prices_raw)} prices")
        
        # Convert dates to datetime objects
        dates = []
        for date_str in dates_raw:
            try:
                # Try different date formats
                date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                dates.append(date_obj)
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    dates.append(date_obj)
                except ValueError:
                    logger.warning(f"Could not parse date: {date_str}")
                    continue
        
        # Filter out zero and negative prices
        valid_data = []
        for i, price in enumerate(prices_raw):
            if i < len(dates) and price > 0:
                valid_data.append((dates[i], float(price)))
        
        if not valid_data:
            raise ValueError("No valid price data found (all prices are zero or negative)")
        
        # Create pandas Series
        dates_clean, prices_clean = zip(*valid_data)
        price_series = pd.Series(prices_clean, index=pd.DatetimeIndex(dates_clean))
        price_series = price_series.sort_index()
        
        logger.info(f"Successfully parsed {len(price_series)} price points")
        return price_series
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON data: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing price series: {e}")


def parse_asset_allocation(js_text: str) -> Dict[str, float]:
    """
    Parse asset allocation data from TEFAS JavaScript content.
    
    Args:
        js_text (str): JavaScript content containing chartMainContent_PieChartFonDagilim
        
    Returns:
        Dict[str, float]: Asset allocation mapping asset names to percentages
        
    Raises:
        ValueError: If required data cannot be found or parsed
    """
    try:
        # Pattern to match chartMainContent_PieChartFonDagilim block
        pie_pattern = r'chartMainContent_PieChartFonDagilim\s*=\s*({.*?});'
        pie_match = re.search(pie_pattern, js_text, re.DOTALL)
        
        if not pie_match:
            raise ValueError("chartMainContent_PieChartFonDagilim block not found in JavaScript")
        
        # Parse the JSON data
        pie_data = json.loads(pie_match.group(1))
        
        # Extract series data for pie chart
        if 'series' not in pie_data or len(pie_data['series']) == 0:
            raise ValueError("Series data not found in pie chart data")
        
        if 'data' not in pie_data['series'][0]:
            raise ValueError("Asset data not found in pie chart series")
        
        asset_data = pie_data['series'][0]['data']
        
        # Build asset allocation dictionary
        allocation = {}
        total_percentage = 0.0
        
        for asset in asset_data:
            if isinstance(asset, dict) and 'name' in asset and 'y' in asset:
                asset_name = asset['name'].strip()
                percentage = float(asset['y'])
                allocation[asset_name] = percentage
                total_percentage += percentage
            elif isinstance(asset, list) and len(asset) >= 2:
                # Handle array format [name, percentage]
                asset_name = str(asset[0]).strip()
                percentage = float(asset[1])
                allocation[asset_name] = percentage
                total_percentage += percentage
        
        if not allocation:
            raise ValueError("No valid asset allocation data found")
        
        # Validate percentages (should sum to ~100%)
        if not (90 <= total_percentage <= 110):
            logger.warning(f"Asset allocation percentages sum to {total_percentage:.2f}%, expected ~100%")
        
        logger.info(f"Successfully parsed asset allocation for {len(allocation)} assets")
        return allocation
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON data: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing asset allocation: {e}")


def parse_benchmark_returns(js_text: str) -> Dict[str, float]:
    """
    Parse benchmark returns data from TEFAS JavaScript content.
    
    Args:
        js_text (str): JavaScript content containing chartMainContent_ColumnChartMatch
        
    Returns:
        Dict[str, float]: Benchmark returns mapping benchmark names to return percentages
        
    Raises:
        ValueError: If required data cannot be found or parsed
    """
    try:
        # Pattern to match chartMainContent_ColumnChartMatch block
        column_pattern = r'chartMainContent_ColumnChartMatch\s*=\s*({.*?});'
        column_match = re.search(column_pattern, js_text, re.DOTALL)
        
        if not column_match:
            raise ValueError("chartMainContent_ColumnChartMatch block not found in JavaScript")
        
        # Parse the JSON data
        column_data = json.loads(column_match.group(1))
        
        # Extract xAxis categories (benchmark names)
        if 'xAxis' not in column_data or 'categories' not in column_data['xAxis']:
            raise ValueError("xAxis categories not found in benchmark data")
        
        benchmark_names = column_data['xAxis']['categories']
        
        # Extract series data (returns)
        if 'series' not in column_data or len(column_data['series']) == 0:
            raise ValueError("Series data not found in benchmark data")
        
        benchmark_returns = {}
        
        # Handle multiple series (e.g., fund vs benchmark comparison)
        for series in column_data['series']:
            if 'data' not in series or 'name' not in series:
                continue
                
            series_name = series['name']
            series_data = series['data']
            
            # Map benchmark names to their returns
            for i, return_value in enumerate(series_data):
                if i < len(benchmark_names):
                    benchmark_name = benchmark_names[i]
                    key = f"{benchmark_name}_{series_name}" if len(column_data['series']) > 1 else benchmark_name
                    
                    if return_value is not None:
                        benchmark_returns[key] = float(return_value)
        
        if not benchmark_returns:
            # Fallback: try to extract data differently
            if len(benchmark_names) > 0 and 'series' in column_data:
                first_series = column_data['series'][0]
                if 'data' in first_series:
                    for i, return_value in enumerate(first_series['data']):
                        if i < len(benchmark_names) and return_value is not None:
                            benchmark_returns[benchmark_names[i]] = float(return_value)
        
        if not benchmark_returns:
            raise ValueError("No valid benchmark return data found")
        
        logger.info(f"Successfully parsed benchmark returns for {len(benchmark_returns)} benchmarks")
        return benchmark_returns
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON data: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing benchmark returns: {e}")



def clean_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate price data.
    
    Args:
        df (pd.DataFrame): Raw price data
    
    Returns:
        pd.DataFrame: Cleaned price data
    """
    if df.empty:
        return df
    
    # Remove rows with zero or negative prices
    df_clean = df[df['Fiyat'] > 0].copy()
    
    # Remove duplicates based on date
    df_clean = df_clean.drop_duplicates(subset=['Tarih'])
    
    # Sort by date
    df_clean = df_clean.sort_values('Tarih').reset_index(drop=True)
    
    # Remove outliers (prices that are more than 10x the median)
    median_price = df_clean['Fiyat'].median()
    if median_price > 0:
        outlier_threshold = median_price * 10
        df_clean = df_clean[df_clean['Fiyat'] <= outlier_threshold]
    
    logger.info(f"Data cleaning: {len(df)} -> {len(df_clean)} records")
    return df_clean


def validate_data_integrity(prices: List[float], dates: List[str]) -> bool:
    """
    Validate that price and date data are consistent.
    
    Args:
        prices (List[float]): List of price values
        dates (List[str]): List of date strings
        
    Returns:
        bool: True if data is valid, False otherwise
    """
    if not prices or not dates:
        return False
    
    if len(prices) != len(dates):
        return False
    
    # Check for valid prices (positive numbers)
    valid_prices = [p for p in prices if isinstance(p, (int, float)) and p > 0]
    if len(valid_prices) < len(prices) * 0.8:  # At least 80% should be valid
        return False
    
    # Check for valid dates
    valid_dates = 0
    for date_str in dates:
        try:
            datetime.strptime(str(date_str), '%d.%m.%Y')
            valid_dates += 1
        except ValueError:
            try:
                datetime.strptime(str(date_str), '%Y-%m-%d')
                valid_dates += 1
            except ValueError:
                continue
    
    if valid_dates < len(dates) * 0.8:  # At least 80% should be valid
        return False
    
    return True
