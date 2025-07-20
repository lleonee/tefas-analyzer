"""
Selenium-based data scraper for TEFAS platform.

This module handles all web scraping operations using Selenium WebDriver
to extract mutual fund data from the TEFAS website.
"""

import re
import time
import logging
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import pandas as pd

from .parser import parse_chart_data, clean_price_data
from ..utils import validate_fund_code, TefasError, ScrapingError

# Logger tanımı (merkezi konfigürasyon api.py'dan gelecek)
logger = logging.getLogger(__name__)


def fetch_tefas_js_blocks(fund_code: str, headless: bool = True) -> Dict[str, str]:
    """
    Fetch JavaScript blocks containing chart data from TEFAS fund page.
    
    Args:
        fund_code (str): The fund code (e.g., "CPU", "AAK", "AFA")
        headless (bool): Whether to run browser in headless mode
        
    Returns:
        Dict[str, str]: Dictionary containing JavaScript blocks:
            - "price": chartMainContent_FonFiyatGrafik block
            - "allocation": chartMainContent_PieChartFonDagilim block  
            - "benchmark": chartMainContent_ColumnChartMatch block
            
    Raises:
        ScrapingError: If scraping fails or fund not found
        ValueError: If fund_code is invalid
    """
    # Validate fund code
    if not fund_code or not isinstance(fund_code, str):
        raise ValueError("Fund code must be a non-empty string")
    
    fund_code = fund_code.strip().upper()
    
    if len(fund_code) < 2 or len(fund_code) > 5:
        raise ValueError("Fund code must be 2-5 characters long")
    
    url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
    driver = None
    
    try:
        logger.info(f"🔄 Starting WebDriver for fund: {fund_code}")
        driver = _setup_chrome_driver(headless=headless)
        
        logger.info(f"🌐 Navigating to TEFAS page: {url}")
        driver.get(url)
        
        # Wait for page to load
        logger.info("⏳ Waiting for page to load...")
        _wait_for_page_load(driver, fund_code)
        
        # Get page source
        logger.info("📄 Extracting page HTML content...")
        html_content = driver.page_source
        
        # Extract JavaScript blocks
        logger.info("🔍 Parsing JavaScript chart blocks...")
        js_blocks = _extract_js_blocks(html_content, fund_code)
        
        logger.info(f"✅ Successfully extracted {len(js_blocks)} JavaScript blocks for {fund_code}")
        return js_blocks
        
    except TimeoutException:
        error_msg = f"Timeout while loading TEFAS page for fund: {fund_code}"
        logger.error(error_msg)
        raise ScrapingError(error_msg)
        
    except NoSuchElementException:
        error_msg = f"Required elements not found on TEFAS page for fund: {fund_code}"
        logger.error(error_msg)
        raise ScrapingError(error_msg)
        
    except WebDriverException as e:
        error_msg = f"WebDriver error for fund {fund_code}: {e}"
        logger.error(error_msg)
        raise ScrapingError(error_msg)
        
    except Exception as e:
        error_msg = f"Unexpected error while scraping fund {fund_code}: {e}"
        logger.error(error_msg)
        raise ScrapingError(error_msg)
        
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("🔄 WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")


def _setup_chrome_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Setup Chrome WebDriver with optimal options for TEFAS scraping.
    
    Args:
        headless (bool): Whether to run in headless mode
        
    Returns:
        webdriver.Chrome: Configured Chrome driver
    """
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless')
    
    # Security and performance options
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument('--disable-javascript-harmony-shipping')
    
    # Window size and user agent
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    # Performance optimizations ve log sessizleştirme
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--log-level=3')  # FATAL only
    chrome_options.add_argument('--silent')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-remote-debugging-port')
    chrome_options.add_argument('--remote-debugging-port=0')  # DevTools tamamen kapat
    
    # WebDriver ve DevTools sessizleştirme
    import os
    os.environ['WDM_LOG_LEVEL'] = '0'  # WebDriverManager loglarını kapat
    
    # Chrome log dosyalarını yönlendir
    chrome_options.add_argument('--log-file=NUL')  # Windows'ta null device
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)  # 30 second timeout
        return driver
    except Exception as e:
        logger.error(f"Failed to create Chrome driver: {e}")
        raise ScrapingError(f"Could not initialize Chrome WebDriver: {e}")


def _wait_for_page_load(driver: webdriver.Chrome, fund_code: str, timeout: int = 20) -> None:
    """
    Wait for the TEFAS fund page to load completely and click 5-year button.
    
    Args:
        driver (webdriver.Chrome): Chrome driver instance
        fund_code (str): Fund code for error reporting
        timeout (int): Maximum wait time in seconds
        
    Raises:
        TimeoutException: If page doesn't load within timeout
        ScrapingError: If fund not found or page has errors
    """
    try:
        logger.info("⏳ Waiting for page to load...")
        
        # Wait for the 5-year period button
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "MainContent_RadioButtonListPeriod_7"))
        )
        
        logger.info("✅ Page loaded, 5-year data button found.")
        
        # Click the "Son 5 Yıl" button
        five_year_button = driver.find_element(By.ID, "MainContent_RadioButtonListPeriod_7")
        driver.execute_script("arguments[0].click();", five_year_button)
        
        logger.info("🔄 5-year data button clicked, loading data...")
        
        # Wait for data to load (page refresh)
        time.sleep(3)
        
        # Wait for chart to load
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "MainContent_FonFiyatGrafik"))
        )
        
        logger.info("✅ Chart loaded, data ready for parsing...")
            
    except TimeoutException:
        raise TimeoutException(f"Page load timeout for fund: {fund_code}")
    except NoSuchElementException:
        raise ScrapingError(f"Required elements not found for fund: {fund_code}")
    except Exception as e:
        raise ScrapingError(f"Error waiting for page load: {e}")


def _extract_js_blocks(html_content: str, fund_code: str) -> Dict[str, str]:
    """
    Extract JavaScript chart blocks from HTML content.
    
    Args:
        html_content (str): Complete HTML page source
        fund_code (str): Fund code for error reporting
        
    Returns:
        Dict[str, str]: Dictionary with extracted JavaScript blocks
        
    Raises:
        ScrapingError: If required blocks cannot be found
    """
    js_blocks = {}
    
    # Define patterns for each chart type
    patterns = {
        "price": r'chartMainContent_FonFiyatGrafik\s*=\s*({.*?});',
        "allocation": r'chartMainContent_PieChartFonDagilim\s*=\s*({.*?});',
        "benchmark": r'chartMainContent_ColumnChartMatch\s*=\s*({.*?});'
    }
    
    blocks_found = 0
    
    for block_name, pattern in patterns.items():
        try:
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                js_blocks[block_name] = match.group(1)
                blocks_found += 1
                logger.debug(f"✅ Found {block_name} block for {fund_code}")
            else:
                logger.warning(f"⚠️ {block_name} block not found for {fund_code}")
                js_blocks[block_name] = None
        except Exception as e:
            logger.warning(f"Error extracting {block_name} block: {e}")
            js_blocks[block_name] = None
    
    # Ensure we found at least the price block (most important)
    if not js_blocks.get("price"):
        raise ScrapingError(f"Critical error: Price data block not found for fund {fund_code}")
    
    logger.info(f"📊 Extracted {blocks_found}/3 JavaScript blocks for {fund_code}")
    return js_blocks


def get_tefas_data(fund_code: str, headless: bool = True) -> pd.DataFrame:
    """
    Get comprehensive TEFAS fund data including price history.
    
    This is the main function that combines scraping and parsing.
    
    Args:
        fund_code (str): The fund code (e.g., "CPU", "AAK", "AFA")
        headless (bool): Whether to run browser in headless mode
        
    Returns:
        pd.DataFrame: DataFrame containing Date and Price columns
        
    Raises:
        ScrapingError: If data cannot be scraped
        ValueError: If fund_code is invalid
    """
    from .parser import parse_chart_data
    
    fund_code = fund_code.strip().upper()
    
    if len(fund_code) < 2 or len(fund_code) > 5:
        raise ValueError("Fund code must be 2-5 characters long")
    
    url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
    driver = None
    
    try:
        logger.info(f"🔄 {fund_code} fund: Starting Selenium WebDriver...")
        driver = _setup_chrome_driver(headless=headless)
        driver.get(url)
        
        logger.info("🔄 Page loading...")
        # Wait for page to load and click 5-year button
        _wait_for_page_load(driver, fund_code)
        
        logger.info("✅ Chart loaded, parsing data...")
        
        # Get page HTML
        html = driver.page_source
        
        # Parse chart data directly from HTML
        df = parse_chart_data(html, fund_code)
        
        if df.empty:
            raise ScrapingError(f"No data found for fund: {fund_code}")
        
        logger.info(f"✅ Successfully extracted {len(df)} records for {fund_code}")
        return df
        
    except TimeoutException:
        error_msg = f"Timeout while loading page for fund: {fund_code}"
        logger.error(error_msg)
        raise ScrapingError(error_msg)
        
    except NoSuchElementException:
        error_msg = f"Required elements not found for fund: {fund_code}"
        logger.error(error_msg)
        raise ScrapingError(error_msg)
        
    except Exception as e:
        error_msg = f"Selenium error for fund {fund_code}: {e}"
        logger.error(error_msg)
        raise ScrapingError(error_msg)
        
    finally:
        if driver:
            driver.quit()
            logger.info("🔄 WebDriver closed.")


def get_fund_additional_data(fund_code: str, headless: bool = True) -> Dict[str, any]:
    """
    Get additional fund data (allocation, benchmark) beyond price history.
    
    Args:
        fund_code (str): The fund code
        headless (bool): Whether to run browser in headless mode
        
    Returns:
        Dict[str, any]: Dictionary containing allocation and benchmark data
    """
    try:
        from .parser import parse_asset_allocation, parse_benchmark_returns
        
        js_blocks = fetch_tefas_js_blocks(fund_code, headless=headless)
        additional_data = {}
        
        # Parse asset allocation
        if js_blocks.get("allocation"):
            try:
                js_content = f"var chartMainContent_PieChartFonDagilim = {js_blocks['allocation']};"
                allocation = parse_asset_allocation(js_content)
                additional_data["asset_allocation"] = allocation
                logger.info(f"✅ Extracted asset allocation for {fund_code}")
            except Exception as e:
                logger.warning(f"Failed to parse asset allocation for {fund_code}: {e}")
                additional_data["asset_allocation"] = {}
        
        # Parse benchmark returns
        if js_blocks.get("benchmark"):
            try:
                js_content = f"var chartMainContent_ColumnChartMatch = {js_blocks['benchmark']};"
                benchmark = parse_benchmark_returns(js_content)
                additional_data["benchmark_returns"] = benchmark
                logger.info(f"✅ Extracted benchmark returns for {fund_code}")
            except Exception as e:
                logger.warning(f"Failed to parse benchmark returns for {fund_code}: {e}")
                additional_data["benchmark_returns"] = {}
        
        return additional_data
        
    except Exception as e:
        logger.error(f"Failed to get additional data for {fund_code}: {e}")
        return {}
