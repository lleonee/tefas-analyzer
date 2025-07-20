#!/usr/bin/env python3
"""
Comprehensive API Tests for TEFAS Analyzer
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add package to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tefas_analyzer as tefas
from tefas_analyzer.utils import validate_fund_code, clean_fund_code, TefasError


class TestAPI:
    """Test suite for main API functions"""
    
    def test_import(self):
        """Test that package imports correctly"""
        assert hasattr(tefas, 'download')
        assert hasattr(tefas, 'get_statistics')
        assert hasattr(tefas, 'analyze')
        assert hasattr(tefas, 'plot_price_chart')
    
    def test_fund_code_validation(self):
        """Test fund code validation"""
        # Valid codes
        assert validate_fund_code('CPU')
        assert validate_fund_code('AAK')
        assert validate_fund_code('AFA')
        
        # Invalid codes
        assert not validate_fund_code('')
        assert not validate_fund_code('123')
        assert not validate_fund_code('TOOLONG')
    
    def test_fund_code_cleaning(self):
        """Test fund code cleaning"""
        assert clean_fund_code('cpu') == 'CPU'
        assert clean_fund_code(' CPU ') == 'CPU'
        assert clean_fund_code('aak') == 'AAK'
    
    @patch('tefas_analyzer.core.scraper.get_tefas_data')
    def test_download_mock(self, mock_scraper):
        """Test download function with mocked data"""
        # Mock DataFrame
        mock_df = pd.DataFrame({
            'Tarih': pd.date_range('2024-01-01', periods=10),
            'Fiyat': np.random.rand(10) + 1.0
        })
        mock_scraper.return_value = mock_df
        
        # Test download
        result = tefas.download('CPU')
        
        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert 'Price' in result.columns
        assert len(result) > 0
        assert pd.api.types.is_datetime64_any_dtype(result.index)
    
    def test_download_validation(self):
        """Test download input validation"""
        with pytest.raises(ValueError):
            tefas.download('')  # Empty code
        
        with pytest.raises(ValueError):
            tefas.download(123)  # Non-string code
    
    @patch('tefas_analyzer.core.scraper.get_tefas_data')
    def test_get_statistics_mock(self, mock_scraper):
        """Test statistics calculation with mock data"""
        # Create test DataFrame
        dates = pd.date_range('2024-01-01', periods=100)
        prices = np.random.rand(100) * 0.1 + 1.0  # Prices around 1.0
        df = pd.DataFrame({
            'Tarih': dates,
            'Fiyat': prices
        })
        df = df.set_index('Tarih')
        df['Price'] = df['Fiyat']
        
        # Test statistics
        stats = tefas.get_statistics(df, 'TEST')
        
        # Verify required fields
        required_fields = [
            'Fon_Kodu', 'Toplam_Getiri_%', 'CAGR_%', 
            'Volatilite_%', 'Sharpe_Ratio'
        ]
        for field in required_fields:
            assert field in stats
        
        # Verify types
        assert isinstance(stats['Toplam_Getiri_%'], (int, float))
        assert isinstance(stats['CAGR_%'], (int, float))
    
    @patch('tefas_analyzer.core.scraper.get_fund_additional_data')
    def test_get_additional_data_mock(self, mock_scraper):
        """Test additional data retrieval"""
        # Mock additional data
        mock_data = {
            'asset_allocation': {'Hisse': 60, 'Tahvil': 40},
            'benchmark_returns': {'1 Ay': 2.5, '1 Yıl': 15.0}
        }
        mock_scraper.return_value = mock_data
        
        # Test function
        result = tefas.get_additional_data('TEST')
        
        # Verify structure
        assert isinstance(result, dict)
        assert 'asset_allocation' in result
        assert 'benchmark_returns' in result


class TestDataFrameFormat:
    """Test DataFrame output format compatibility"""
    
    @patch('tefas_analyzer.core.scraper.get_tefas_data')
    def test_yfinance_compatibility(self, mock_scraper):
        """Test yfinance-like DataFrame format"""
        # Mock valid data
        mock_df = pd.DataFrame({
            'Tarih': pd.date_range('2024-01-01', periods=50),
            'Fiyat': np.random.rand(50) + 1.0
        })
        mock_scraper.return_value = mock_df
        
        # Get DataFrame
        df = tefas.download('TEST')
        
        # Test yfinance compatibility
        assert pd.api.types.is_datetime64_any_dtype(df.index)  # DateTime index
        assert 'Price' in df.columns  # Price column
        assert pd.api.types.is_numeric_dtype(df['Price'])  # Numeric price
        assert not df['Price'].isna().any()  # No NaN values
        assert df.index.is_monotonic_increasing  # Sorted by date
        
        # Test yfinance-like operations
        latest = df['Price'].iloc[-1]
        assert isinstance(latest, (int, float))
        
        # Test date slicing
        recent = df.loc['2024-01-15':]
        assert len(recent) > 0


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_fund_codes(self):
        """Test handling of invalid fund codes"""
        invalid_codes = ['', '123', 'TOOLONG', None, 123]
        
        for code in invalid_codes:
            with pytest.raises((ValueError, TypeError)):
                tefas.download(code)
    
    @patch('tefas_analyzer.core.scraper.get_tefas_data')
    def test_empty_dataframe(self, mock_scraper):
        """Test handling of empty data"""
        # Mock empty DataFrame
        mock_scraper.return_value = pd.DataFrame()
        
        with pytest.raises(TefasError):
            tefas.download('TEST')
    
    @patch('tefas_analyzer.core.scraper.get_tefas_data')
    def test_malformed_data(self, mock_scraper):
        """Test handling of malformed data"""
        # Mock DataFrame with wrong columns
        mock_df = pd.DataFrame({
            'Wrong_Column': [1, 2, 3],
            'Another_Wrong': ['a', 'b', 'c']
        })
        mock_scraper.return_value = mock_df
        
        with pytest.raises(TefasError):
            tefas.download('TEST')

    @patch('tefas_analyzer.core.scraper.get_tefas_data')
    def test_download_with_date_range(self, mock_scraper):
        """Test download function with start/end date filtering"""
        # Mock DataFrame
        mock_df = pd.DataFrame({
            'Tarih': pd.date_range('2024-01-01', periods=10),
            'Fiyat': np.random.rand(10) + 1.0
        })
        mock_scraper.return_value = mock_df

        # Test with start and end
        result = tefas.download('CPU', start='2024-01-04', end='2024-01-07')
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        # Tüm tarihler aralıkta olmalı
        assert result.index.min() >= pd.to_datetime('2024-01-04')
        assert result.index.max() <= pd.to_datetime('2024-01-07')
        # Doğru satır sayısı
        expected_dates = pd.date_range('2024-01-04', '2024-01-07')
        assert len(result) == len(expected_dates)


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, '-v'])
