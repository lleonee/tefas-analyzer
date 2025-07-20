"""
Data visualization and plotting utilities using matplotlib.

This module provides beautiful and informative charts for mutual fund analysis,
including price charts, return distributions, and comparison plots.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path

# Logger tanımı (merkezi konfigürasyon api.py'dan gelecek)
logger = logging.getLogger(__name__)

# Configure matplotlib for Turkish locale and better appearance
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 11
plt.rcParams['figure.dpi'] = 100


def plot_fund_chart(price_series: pd.Series, fund_code: str = "", show: bool = True, 
                   save_path: Optional[str] = None) -> None:
    """
    Create a comprehensive fund price chart.
    
    Args:
        price_series (pd.Series): Price data with datetime index
        fund_code (str): Fund code for chart title
        show (bool): Whether to display the chart
        save_path (Optional[str]): Path to save the chart as PNG
        
    Raises:
        ValueError: If price_series is invalid
        IOError: If saving fails
    """
    try:
        # Input validation
        if not isinstance(price_series, pd.Series):
            raise ValueError("price_series must be a pandas Series")
        
        if len(price_series) < 2:
            raise ValueError("price_series must contain at least 2 data points")
        
        if not isinstance(price_series.index, pd.DatetimeIndex):
            raise ValueError("price_series must have a DatetimeIndex")
        
        if price_series.isnull().any():
            logger.warning("price_series contains NaN values, they will be dropped")
            price_series = price_series.dropna()
        
        if (price_series <= 0).any():
            logger.warning("price_series contains non-positive values")
        
        # Sort by index to ensure chronological order
        price_series = price_series.sort_index()
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Plot the price line
        ax.plot(price_series.index, price_series.values, 
               color='darkblue', linewidth=2.5, alpha=0.8)
        
        # Customize the chart
        ax.set_title(f"{fund_code} Fiyat Grafiği")
        ax.set_xlabel("Tarih")
        ax.set_ylabel("Fiyat")
        
        # Configure grid
        ax.grid(True, linestyle='--', alpha=0.6, color='gray')
        ax.set_axisbelow(True)
        
        # Format dates on x-axis (Turkish format: dd.mm.yyyy)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        
        # Rotate date labels for better readability
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Set y-axis limits with some padding
        min_price = price_series.min()
        max_price = price_series.max()
        price_range = max_price - min_price
        
        if price_range > 0:
            y_margin = price_range * 0.05  # 5% margin
            ax.set_ylim(min_price - y_margin, max_price + y_margin)
        
        # Calculate and display performance metrics
        if len(price_series) >= 2:
            _add_performance_annotations(ax, price_series, fund_code)
        
        # Improve layout
        plt.tight_layout()
        
        # Save chart if path provided
        if save_path:
            try:
                # Ensure directory exists
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save with high DPI
                plt.savefig(save_path, dpi=150, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                logger.info(f"Chart saved to: {save_path}")
            except Exception as e:
                logger.error(f"Failed to save chart: {e}")
                raise IOError(f"Could not save chart to {save_path}: {e}")
        
        # Show chart if requested
        if show:
            plt.show()
        else:
            plt.close()
            
        logger.info(f"Chart created successfully for {fund_code}")
        
    except Exception as e:
        logger.error(f"Error creating chart for {fund_code}: {e}")
        if plt.get_fignums():  # If a figure was created
            plt.close()
        raise


def _add_performance_annotations(ax: plt.Axes, price_series: pd.Series, fund_code: str) -> None:
    """
    Add performance metrics as text annotations to chart.
    
    Args:
        ax (plt.Axes): Matplotlib axes object
        price_series (pd.Series): Price data
        fund_code (str): Fund code
    """
    try:
        # Calculate performance metrics
        initial_price = price_series.iloc[0]
        final_price = price_series.iloc[-1]
        total_return = ((final_price - initial_price) / initial_price) * 100
        
        min_price = price_series.min()
        max_price = price_series.max()
        
        # Determine return color and symbol
        return_color = "lightgreen" if total_return >= 0 else "lightcoral"
        return_symbol = "📈" if total_return >= 0 else "📉"
        
        # Add performance box
        performance_text = f"{return_symbol} Toplam Getiri: %{total_return:.2f}"
        ax.text(0.02, 0.95, performance_text, transform=ax.transAxes, 
               fontsize=12, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.4", facecolor=return_color, alpha=0.8))
        
        # Add price info boxes
        price_info = [
            f"💰 İlk Fiyat: {initial_price:.4f} TL",
            f"💰 Son Fiyat: {final_price:.4f} TL",
            f"📊 Min: {min_price:.4f} | Max: {max_price:.4f} TL"
        ]
        
        y_positions = [0.88, 0.82, 0.76]
        for i, info in enumerate(price_info):
            ax.text(0.02, y_positions[i], info, transform=ax.transAxes, 
                   fontsize=10,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
        
        # Add data period info
        start_date = price_series.index[0].strftime('%d.%m.%Y')
        end_date = price_series.index[-1].strftime('%d.%m.%Y')
        period_text = f"📅 Dönem: {start_date} - {end_date}"
        
        ax.text(0.02, 0.70, period_text, transform=ax.transAxes, 
               fontsize=9,
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.7))
        
    except Exception as e:
        logger.warning(f"Could not add performance annotations: {e}")


def plot_returns_distribution(returns: pd.Series, fund_code: str = "", show: bool = True,
                             save_path: Optional[str] = None) -> None:
    """
    Plot histogram of daily returns.
    
    Args:
        returns (pd.Series): Daily returns series
        fund_code (str): Fund code for chart title
        show (bool): Whether to display the chart
        save_path (Optional[str]): Path to save the chart
    """
    try:
        if not isinstance(returns, pd.Series):
            raise ValueError("returns must be a pandas Series")
        
        if len(returns) < 10:
            raise ValueError("returns must contain at least 10 data points")
        
        # Remove NaN and infinite values
        returns_clean = returns.replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(returns_clean) == 0:
            raise ValueError("No valid returns data after cleaning")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot histogram
        n_bins = min(50, len(returns_clean) // 5)  # Adaptive bin count
        ax.hist(returns_clean * 100, bins=n_bins, alpha=0.7, color='steelblue', 
               edgecolor='black', linewidth=0.5)
        
        # Add vertical line at zero
        ax.axvline(x=0, color='red', linestyle='--', linewidth=2, alpha=0.8)
        
        # Customize chart
        ax.set_title(f"{fund_code} Günlük Getiri Dağılımı")
        ax.set_xlabel("Günlük Getiri (%)")
        ax.set_ylabel("Frekans")
        ax.grid(True, alpha=0.3)
        
        # Add statistics
        mean_return = returns_clean.mean() * 100
        std_return = returns_clean.std() * 100
        
        stats_text = f"Ortalama: {mean_return:.3f}%\nStd. Sapma: {std_return:.3f}%"
        ax.text(0.75, 0.95, stats_text, transform=ax.transAxes, 
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))
        
        plt.tight_layout()
        
        # Save and/or show
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Returns distribution chart saved to: {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
            
    except Exception as e:
        logger.error(f"Error creating returns distribution chart: {e}")
        if plt.get_fignums():
            plt.close()
        raise


def plot_comparison_chart(fund_data: Dict[str, pd.Series], show: bool = True,
                         save_path: Optional[str] = None) -> None:
    """
    Plot multiple funds for comparison.
    
    Args:
        fund_data (Dict[str, pd.Series]): Dictionary mapping fund codes to price series
        show (bool): Whether to display the chart
        save_path (Optional[str]): Path to save the chart
    """
    try:
        if not fund_data:
            raise ValueError("fund_data cannot be empty")
        
        if len(fund_data) > 10:
            logger.warning("Too many funds for comparison, chart may be crowded")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Colors for different funds
        colors = ['darkblue', 'darkred', 'darkgreen', 'darkorange', 'purple', 
                 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        # Normalize all series to start at 100 for comparison
        for i, (fund_code, price_series) in enumerate(fund_data.items()):
            if len(price_series) < 2:
                logger.warning(f"Skipping {fund_code}: insufficient data")
                continue
            
            # Normalize to 100 at start
            normalized_series = (price_series / price_series.iloc[0]) * 100
            
            color = colors[i % len(colors)]
            ax.plot(normalized_series.index, normalized_series.values, 
                   label=fund_code, color=color, linewidth=2, alpha=0.8)
        
        # Customize chart
        ax.set_title("Fon Karşılaştırması (Normalized)")
        ax.set_xlabel("Tarih")
        ax.set_ylabel("Normalized Fiyat (Başlangıç = 100)")
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=10)
        
        # Format dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save and/or show
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Comparison chart saved to: {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
            
    except Exception as e:
        logger.error(f"Error creating comparison chart: {e}")
        if plt.get_fignums():
            plt.close()
        raise


def setup_chart_style() -> None:
    """Configure matplotlib style for professional-looking charts."""
    plt.style.use('default')  # Start with default style
    
    # Set custom parameters
    plt.rcParams.update({
        'figure.figsize': (12, 8),
        'font.size': 10,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 11,
        'figure.dpi': 100,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'lines.linewidth': 2,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white'
    })
    
    logger.info("Chart style configured for professional appearance")


# Initialize chart style when module is imported
setup_chart_style()
