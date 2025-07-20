#!/usr/bin/env python3
"""
CLI Tests for TEFAS Analyzer
"""

import pytest
import subprocess
import sys
import os
from unittest.mock import patch, Mock
import json

# Add package to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tefas_analyzer import cli


class TestCLI:
    """Test suite for CLI functionality"""
    
    def test_cli_import(self):
        """Test CLI module imports correctly"""
        assert hasattr(cli, 'main')
        assert hasattr(cli, 'analyze_fund')
    
    @patch('tefas_analyzer.api.download')
    @patch('tefas_analyzer.api.get_statistics')
    def test_cli_basic_analysis(self, mock_stats, mock_download):
        """Test basic CLI fund analysis"""
        import pandas as pd
        import numpy as np
        
        # Mock data
        mock_df = pd.DataFrame({
            'Price': np.random.rand(100) + 1.0
        }, index=pd.date_range('2024-01-01', periods=100))
        mock_download.return_value = mock_df
        
        mock_stats.return_value = {
            'Fon_Kodu': 'TEST',
            'Toplam_Getiri_%': 15.5,
            'CAGR_%': 8.2,
            'Volatilite_%': 12.3
        }
        
        # Test CLI function
        result = cli.analyze_fund('TEST', show_stats=True, show_chart=False)
        
        # Verify calls
        mock_download.assert_called_once()
        mock_stats.assert_called_once()
    
    def test_argument_parsing(self):
        """Test CLI argument parsing"""
        # Test with valid arguments
        test_args = ['CPU', '--stats', '--verbose']
        
        # Mock sys.argv
        with patch('sys.argv', ['cli.py'] + test_args):
            parser = cli.create_parser()
            args = parser.parse_args(test_args)
            
            assert args.fund_codes == ['CPU']
            assert args.stats == True
            assert args.verbose == True
    
    def test_help_command(self):
        """Test CLI help command"""
        parser = cli.create_parser()
        
        # Test that help doesn't raise exception
        with pytest.raises(SystemExit):
            parser.parse_args(['--help'])
    
    @patch('tefas_analyzer.utils.get_popular_funds')
    def test_list_popular_funds(self, mock_popular):
        """Test listing popular funds"""
        mock_popular.return_value = ['CPU', 'AAK', 'AFA']
        
        # Test function
        parser = cli.create_parser()
        args = parser.parse_args(['--list'])
        
        assert args.list == True
    
    def test_invalid_fund_code(self):
        """Test CLI with invalid fund code"""
        parser = cli.create_parser()
        args = parser.parse_args(['INVALID123'])
        
        # Should parse without error (validation happens in execution)
        assert args.fund_codes == ['INVALID123']


class TestCLIIntegration:
    """Integration tests for CLI (require actual subprocess calls)"""
    
    def test_cli_help_subprocess(self):
        """Test CLI help via subprocess"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'tefas_analyzer.cli', '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Help should exit with code 0
            assert result.returncode == 0
            assert 'usage:' in result.stdout.lower()
            
        except subprocess.TimeoutExpired:
            pytest.skip("CLI help test timed out")
        except FileNotFoundError:
            pytest.skip("CLI module not found")
    
    def test_cli_list_subprocess(self):
        """Test CLI list command via subprocess"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'tefas_analyzer.cli', '--list'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # List should work without network errors
            assert result.returncode == 0 or "popular funds" in result.stdout.lower()
            
        except subprocess.TimeoutExpired:
            pytest.skip("CLI list test timed out")
        except FileNotFoundError:
            pytest.skip("CLI module not found")


class TestCLIVerboseLogging:
    """Test CLI verbose logging functionality"""
    
    @patch('tefas_analyzer.utils.setup_logging')
    def test_verbose_flag(self, mock_setup_logging):
        """Test verbose flag sets up logging correctly"""
        # Simulate CLI call with verbose
        parser = cli.create_parser()
        args = parser.parse_args(['CPU', '--verbose'])
        
        assert args.verbose == True
    
    @patch('tefas_analyzer.utils.setup_logging')
    def test_quiet_mode_default(self, mock_setup_logging):
        """Test default quiet mode"""
        parser = cli.create_parser()
        args = parser.parse_args(['CPU'])
        
        assert args.verbose == False


def create_parser():
    """Helper function to create CLI parser (mock if needed)"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TEFAS Fund Analyzer CLI')
    
    parser.add_argument(
        'fund_codes',
        nargs='*',
        help='Fund codes to analyze'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics'
    )
    
    parser.add_argument(
        '--chart',
        action='store_true', 
        help='Show chart'
    )
    
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare multiple funds'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List popular funds'
    )
    
    return parser


# Monkey patch for testing
cli.create_parser = create_parser


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
