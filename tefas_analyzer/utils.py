# Utility functions and helpers for TEFAS Fund Analyzer
"""
Utility functions and helper classes for TEFAS Fund Analyzer.

This module contains common utility functions, constants, and helper classes
used across the entire package.
"""

from typing import List, Dict, Any, Optional
import re
import logging
from datetime import datetime, timedelta

# Popular TEFAS fund codes
POPULAR_FUNDS = {
    "CPU": "Garanti Portföy Teknoloji",
    "AAK": "Ak Portföy Konut Gayrimenkul", 
    "AFA": "Ak Portföy Altın Katılım",
    "GAH": "Garanti Portföy Altın",
    "TKB": "Taksit Endeksi",
    "YAS": "Yapı Kredi Portföy Altın",
    "APE": "Ak Portföy Petrol",
    "GMF": "Garanti Portföy Büyüme",
    "GPB": "Garanti Portföy Birinci",
    "AEF": "Ak Portföy Enflasyon Korumalı"
}

def validate_fund_code(fund_code: str) -> bool:
    """
    Validate fund code format.
    
    Args:
        fund_code (str): Fund code to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not fund_code or not isinstance(fund_code, str):
        return False
    
    # Clean the fund code
    cleaned_code = fund_code.strip().upper()
    
    # TEFAS fund codes are typically 2-5 characters, alphanumeric
    if len(cleaned_code) < 2 or len(cleaned_code) > 5:
        return False
    
    # Should contain only letters and numbers (no special characters)
    if not re.match(r'^[A-Z0-9]+$', cleaned_code):
        return False
    
    return True

def get_popular_funds() -> Dict[str, str]:
    """Get dictionary of popular TEFAS funds."""
    return POPULAR_FUNDS

def format_percentage(value: float, decimal_places: int = 2) -> str:
    """Format a decimal as percentage string."""
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return f"{value:.{decimal_places}f}%"

def format_currency(value: float, currency: str = "TL") -> str:
    """Format a number as currency string."""
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return f"{value:.4f} {currency}"

def calculate_date_range(years: int = 5) -> tuple:
    """Calculate date range for data collection."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    return start_date, end_date

def clean_fund_code(fund_code: str) -> str:
    """Clean and normalize fund code."""
    if not fund_code or not isinstance(fund_code, str):
        return ""
    
    # Remove whitespace and convert to uppercase
    cleaned = fund_code.strip().upper()
    
    # Remove any non-alphanumeric characters
    cleaned = re.sub(r'[^A-Z0-9]', '', cleaned)
    
    return cleaned

def setup_logging(verbose: bool = False) -> None:
    """
    Setup centralized logging configuration for TEFAS Analyzer.
    
    Normal kullanımda sadece WARNING ve ERROR çıktıları gösterilir.
    verbose=True ile DEBUG ve INFO çıktıları da etkinleştirilir.
    
    Args:
        verbose (bool): Enable verbose logging (DEBUG/INFO levels)
    """
    # Ana uygulama log seviyesi
    if verbose:
        app_level = logging.DEBUG
        root_level = logging.DEBUG
    else:
        app_level = logging.WARNING
        root_level = logging.WARNING
    
    # Root logger konfigürasyonu
    logging.basicConfig(
        level=root_level,
        format='%(levelname)s - %(message)s',
        force=True  # Mevcut konfigürasyonu zorla sıfırla
    )
    
    # TEFAS Analyzer modüllerinin log seviyesini ayarla
    tefas_logger = logging.getLogger('tefas_analyzer')
    tefas_logger.setLevel(app_level)
    
    # Selenium WebDriver loglarını sessizleştir
    selenium_loggers = [
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.remote.remote_connection',
        'selenium.webdriver.common.selenium_manager',
        'urllib3.connectionpool'
    ]
    
    for logger_name in selenium_loggers:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    # Chrome driver loglarını sessizleştir  
    logging.getLogger('WDM').setLevel(logging.ERROR)
    
    if verbose:
        logging.getLogger('tefas_analyzer').info("🔧 Verbose logging enabled")
    
    return tefas_logger

class TefasError(Exception):
    """Base exception for TEFAS-related errors."""
    pass

class ScrapingError(TefasError):
    """Exception for web scraping related errors."""
    pass

def safe_format(template: str, **kwargs) -> str:
    """Safe string formatting that handles missing keys gracefully."""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"Format error: missing key {e}"

class ScrapingError(TefasError):
    """Exception raised when web scraping fails."""
    pass

class ScrapingError(TefasError):
    """Exception raised when web scraping fails."""
    pass

class DataParsingError(TefasError):
    """Exception raised when data parsing fails."""
    pass

class ValidationError(TefasError):
    """Exception raised when data validation fails."""
    pass
