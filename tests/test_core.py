#!/usr/bin/env python3
"""
Tests for Core Modules (Analytics, Parser, Scraper, Plotter)
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add package to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tefas_analyzer.core import analytics, parser, scraper, plotter
from tefas_analyzer.utils import TefasError


class TestAnalytics:
    """Test financial analytics functions"""
    
    def setup_method(self):
        """Setup test data"""
        np.random.seed(42)  # For reproducible tests
        dates = pd.date_range('2024-01-01', periods=100)
        prices = np.random.rand(100) * 0.2 + 1.0  # Prices around 1.0-1.2
        self.test_df = pd.DataFrame({'Price': prices}, index=dates)
        self.price_series = self.test_df['Price']
    
    def test_total_return_calculation(self):
        """Test total return calculation"""
        result = analytics.calculate_total_return(self.price_series)
        
        assert isinstance(result, (int, float))
        assert not np.isnan(result)
        assert -100 <= result <= 1000  # Reasonable range for returns
    
    def test_volatility_calculation(self):
        """Test volatility calculation"""
        result = analytics.calculate_volatility(self.price_series)
        
        assert isinstance(result, (int, float))
        assert result >= 0  # Volatility is always positive
        assert not np.isnan(result)
    
    def test_cagr_calculation(self):
        """Test CAGR calculation"""
        result = analytics.calculate_cagr(self.price_series)
        
        assert isinstance(result, (int, float))
        assert not np.isnan(result)
    
    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation"""
        result = analytics.calculate_sharpe_ratio(self.price_series)
        
        assert isinstance(result, (int, float))
        # Sharpe ratio can be negative, so no range check
        assert not np.isnan(result)
    
    def test_empty_series(self):
        """Test analytics with empty series"""
        empty_series = pd.Series([], dtype=float)
        
        with pytest.raises((ValueError, ZeroDivisionError)):
            analytics.calculate_total_return(empty_series)
    
    def test_single_value_series(self):
        """Test analytics with single value"""
        single_series = pd.Series([1.0])
        
        # Should handle single value gracefully
        result = analytics.calculate_total_return(single_series)
        assert result == 0.0  # No change = 0% return


class TestParser:
    """Test HTML/JavaScript parsing functions"""
    
    def test_extract_price_data(self):
        """Test price data extraction from JavaScript"""
        # Mock JavaScript content
        js_content = '''
        var priceData = [
            [1704067200000, 1.2345],
            [1704153600000, 1.2400],
            [1704240000000, 1.2450]
        ];
        '''
        
        result = parser.extract_price_data_from_js(js_content, 'TEST')
        
        assert isinstance(result, pd.DataFrame)
        assert 'Tarih' in result.columns
        assert 'Fiyat' in result.columns
        assert len(result) > 0
    
    def test_clean_price_data(self):
        """Test price data cleaning"""
        # Create test data with issues
        dirty_df = pd.DataFrame({
            'Tarih': pd.date_range('2024-01-01', periods=10),
            'Fiyat': [1.0, 0.0, 1.1, -0.5, 1.2, np.nan, 1.3, 0.0, 1.4, 1.5]
        })
        
        clean_df = parser.clean_price_data(dirty_df, 'TEST')
        
        # Should remove zero, negative, and NaN values
        assert len(clean_df) < len(dirty_df)
        assert all(clean_df['Fiyat'] > 0)
        assert not clean_df['Fiyat'].isna().any()
    
    def test_invalid_javascript(self):
        """Test handling of invalid JavaScript"""
        invalid_js = "This is not valid JavaScript content"
        
        # Should handle gracefully
        result = parser.extract_price_data_from_js(invalid_js, 'TEST')
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0  # Empty result for invalid JS


class TestScraper:
    """Test web scraping functions (mocked)"""
    
    @patch('selenium.webdriver.Chrome')
    def test_create_chrome_driver(self, mock_chrome):
        """Test Chrome driver creation"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        driver = scraper._create_chrome_driver(headless=True)
        
        assert driver is not None
        mock_chrome.assert_called_once()
    
    def test_fund_code_validation(self):
        """Test fund code validation in scraper"""
        from tefas_analyzer.utils import validate_fund_code
        
        # Valid codes
        assert validate_fund_code('CPU')
        assert validate_fund_code('AAK')
        
        # Invalid codes
        assert not validate_fund_code('')
        assert not validate_fund_code('123')
    
    @patch('tefas_analyzer.core.scraper._create_chrome_driver')
    @patch('tefas_analyzer.core.scraper._wait_for_page_load')
    def test_scraping_workflow(self, mock_wait, mock_driver):
        """Test scraping workflow (mocked)"""
        # Mock driver and page content
        mock_driver_instance = Mock()
        mock_driver_instance.page_source = """
        <html>
            <script>
                var priceData = [[1704067200000, 1.234]];
            </script>
        </html>
        """
        mock_driver.return_value = mock_driver_instance
        
        # This would normally call the network, so we mock it
        with patch('tefas_analyzer.core.parser.parse_chart_data') as mock_parser:
            mock_df = pd.DataFrame({
                'Tarih': [pd.Timestamp('2024-01-01')],
                'Fiyat': [1.234]
            })
            mock_parser.return_value = mock_df
            
            # Test would go here - but requires full integration


class TestPlotter:
    """Test plotting functions"""
    
    def setup_method(self):
        """Setup test data"""
        dates = pd.date_range('2024-01-01', periods=50)
        prices = np.random.rand(50) * 0.1 + 1.0
        self.test_df = pd.DataFrame({'Price': prices}, index=dates)
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.savefig')
    def test_price_chart_creation(self, mock_savefig, mock_show):
        """Test price chart creation"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-GUI backend
            
            plotter.create_price_chart(
                self.test_df['Price'], 
                'TEST', 
                show=False
            )
            
            # Should not raise exception
            assert True
            
        except ImportError:
            pytest.skip("Matplotlib not available")
    
    @patch('matplotlib.pyplot.show')
    def test_comparison_chart(self, mock_show):
        """Test fund comparison chart"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            
            # Create comparison data
            fund_data = {
                'TEST1': self.test_df['Price'],
                'TEST2': self.test_df['Price'] * 1.1
            }
            
            plotter.create_comparison_chart(fund_data, show=False)
            
            # Should not raise exception
            assert True
            
        except ImportError:
            pytest.skip("Matplotlib not available")
    
    def test_invalid_data_handling(self):
        """Test handling of invalid plotting data"""
        # Empty DataFrame
        empty_df = pd.DataFrame()
        
        # Should handle gracefully
        try:
            plotter.create_price_chart(pd.Series([]), 'TEST', show=False)
            # Should either work or raise appropriate exception
        except (ValueError, TypeError):
            # Expected for empty data
            pass


class TestUtilities:
    """Test utility functions"""
    
    def test_fund_code_validation(self):
        """Test fund code validation utility"""
        from tefas_analyzer.utils import validate_fund_code
        
        # Valid codes
        valid_codes = ['CPU', 'AAK', 'AFA', 'ABC']
        for code in valid_codes:
            assert validate_fund_code(code)
        
        # Invalid codes
        invalid_codes = ['', '123', 'TOOLONG', 'ab', '12A']
        for code in invalid_codes:
            assert not validate_fund_code(code)
    
    def test_fund_code_cleaning(self):
        """Test fund code cleaning utility"""
        from tefas_analyzer.utils import clean_fund_code
        
        test_cases = [
            ('cpu', 'CPU'),
            (' AAK ', 'AAK'),
            ('afa', 'AFA'),
            ('CPU', 'CPU')
        ]
        
        for input_code, expected in test_cases:
            assert clean_fund_code(input_code) == expected
    
    def test_custom_exceptions(self):
        """Test custom exception classes"""
        from tefas_analyzer.utils import TefasError, ScrapingError
        
        # Test exception hierarchy
        assert issubclass(ScrapingError, TefasError)
        
        # Test exception creation
        error = TefasError("Test error")
        assert str(error) == "Test error"
        
        scraping_error = ScrapingError("Scraping failed")
        assert str(scraping_error) == "Scraping failed"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
