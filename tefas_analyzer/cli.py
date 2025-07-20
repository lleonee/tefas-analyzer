"""
Command Line Interface for TEFAS Fund Analyzer.

This module provides a clean, yfinance-like CLI interface using the api.py module.
All operations are routed through the unified API for consistency and simplicity.
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd

# Import the unified API
from . import api
from .utils import get_popular_funds, clean_fund_code, TefasError, ScrapingError, setup_logging

# Logger tanımı (konfigürasyon main'de yapılacak)
logger = logging.getLogger(__name__)


def display_fund_stats(fund_code: str, stats: Dict[str, Any]) -> None:
    """
    Display fund statistics in a user-friendly format with emojis.
    
    Args:
        fund_code (str): Fund code
        stats (Dict[str, Any]): Statistics dictionary from api.get_statistics()
    """
    print(f"\n📊 {fund_code} FONU ANALİZİ")
    print("=" * 60)
    
    # Basic info
    if stats.get('Ilk_Tarih') and stats.get('Son_Tarih'):
        print(f"📅 Analiz Dönemi: {stats['Ilk_Tarih'].strftime('%d.%m.%Y')} - {stats['Son_Tarih'].strftime('%d.%m.%Y')}")
        gun_farki = (stats['Son_Tarih'] - stats['Ilk_Tarih']).days
        yil_farki = gun_farki / 365.25
        print(f"⏱️  Toplam Süre: {gun_farki} gün ({yil_farki:.1f} yıl)")
    
    print("=" * 60)
    
    # Price information
    if stats.get('Ilk_Fiyat') is not None:
        print(f"💰 İlk Fiyat: {stats['Ilk_Fiyat']:.4f} TL")
    if stats.get('Son_Fiyat') is not None:
        print(f"💰 Son Fiyat: {stats['Son_Fiyat']:.4f} TL")
    if stats.get('Min_Fiyat') is not None:
        print(f"📈 Minimum Fiyat: {stats['Min_Fiyat']:.4f} TL")
    if stats.get('Max_Fiyat') is not None:
        print(f"📈 Maksimum Fiyat: {stats['Max_Fiyat']:.4f} TL")
    if stats.get('Ortalama_Fiyat') is not None:
        print(f"📊 Ortalama Fiyat: {stats['Ortalama_Fiyat']:.4f} TL")
    
    print("\n" + "=" * 60)
    
    # Performance metrics
    if stats.get('Toplam_Getiri_%') is not None:
        getiri = stats['Toplam_Getiri_%']
        getiri_sembol = "📈" if getiri >= 0 else "📉"
        getiri_renk = "🟢" if getiri >= 0 else "🔴"
        print(f"{getiri_sembol} Toplam Getiri: {getiri_renk} %{getiri:.2f}")
    
    if stats.get('CAGR_%') is not None:
        print(f"📅 Yıllık Ortalama Getiri (CAGR): %{stats['CAGR_%']:.2f}")
    
    print("\n" + "=" * 60)
    
    # Risk metrics
    if stats.get('Volatilite_%') is not None:
        volatilite = stats['Volatilite_%']
        volatilite_renk = "🟢" if volatilite < 15 else "🟡" if volatilite < 25 else "🔴"
        print(f"⚡ Volatilite (Risk): {volatilite_renk} %{volatilite:.2f}")
    
    if stats.get('Sharpe_Ratio') is not None:
        sharpe = stats['Sharpe_Ratio']
        sharpe_renk = "🟢" if sharpe > 1 else "🟡" if sharpe > 0.5 else "🔴"
        print(f"📊 Sharpe Oranı: {sharpe_renk} {sharpe:.3f}")
    
    if stats.get('Veri_Sayisi') is not None:
        print(f"📊 Temiz Veri Sayısı: {stats['Veri_Sayisi']} gün")
    
    # Performance evaluation
    print("\n💡 PERFORMANS YORUMU:")
    if stats.get('CAGR_%') is not None:
        yillik_getiri = stats['CAGR_%']
        if yillik_getiri > 20:
            print("🚀 Mükemmel performans! Yıllık %20'nin üzerinde getiri.")
        elif yillik_getiri > 10:
            print("✅ Çok iyi performans! Yıllık %10'un üzerinde getiri.")
        elif yillik_getiri > 0:
            print("👍 Pozitif performans! Para kazandıran bir yatırım.")
        else:
            print("⚠️ Negatif performans! Zarar eden bir yatırım.")
    
    print("=" * 60)


def display_additional_data(fund_code: str, additional_data: Dict[str, Any]) -> None:
    """
    Display additional fund data (asset allocation, benchmark returns).
    
    Args:
        fund_code (str): Fund code
        additional_data (Dict[str, Any]): Additional data from api.get_additional_data()
    """
    # Asset allocation
    if additional_data.get('asset_allocation'):
        allocation = additional_data['asset_allocation']
        print(f"\n🧩 {fund_code} VARLIK DAĞILIMI")
        print("=" * 40)
        for asset, percentage in allocation.items():
            print(f"  • {asset}: %{percentage:.1f}")
    
    # Benchmark returns
    if additional_data.get('benchmark_returns'):
        benchmark = additional_data['benchmark_returns']
        print(f"\n📊 {fund_code} BENCHMARK KARŞILAŞTIRMASI")
        print("=" * 40)
        for period, return_val in benchmark.items():
            print(f"  • {period}: %{return_val:.2f}")


def save_results_to_file(results: Dict[str, Any], filename: str, format_type: str) -> None:
    """
    Save analysis results to file.
    
    Args:
        results (Dict[str, Any]): Analysis results
        filename (str): Output filename
        format_type (str): Output format ('json' or 'csv')
    """
    try:
        if format_type.lower() == 'json':
            # Handle datetime objects for JSON serialization
            json_results = {}
            for key, value in results.items():
                if hasattr(value, 'strftime'):  # datetime object
                    json_results[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif pd.isna(value):  # Handle NaN values
                    json_results[key] = None
                else:
                    json_results[key] = value
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_results, f, indent=2, ensure_ascii=False)
            print(f"✅ Sonuçlar JSON formatında kaydedildi: {filename}")
        
        elif format_type.lower() == 'csv':
            # Convert to DataFrame for CSV export
            df = pd.DataFrame([results])
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Sonuçlar CSV formatında kaydedildi: {filename}")
        
        else:
            print(f"❌ Desteklenmeyen format: {format_type}")
    
    except Exception as e:
        print(f"❌ Dosya kaydetme hatası: {e}")


def analyze_fund(fund_code: str, show_chart: bool = False, show_stats: bool = True, 
                output_file: Optional[str] = None, output_format: str = 'json') -> bool:
    """
    Analyze a single fund using the unified API.
    
    Args:
        fund_code (str): Fund code to analyze
        show_chart (bool): Whether to display chart
        show_stats (bool): Whether to display statistics
        output_file (Optional[str]): Output file path
        output_format (str): Output format ('json' or 'csv')
    
    Returns:
        bool: True if analysis was successful, False otherwise
    """
    try:
        # Clean and validate fund code
        fund_code = clean_fund_code(fund_code)
        logger.info(f"Starting analysis for fund: {fund_code}")
        
        print(f"\n🎯 {fund_code} fonu analiz ediliyor...")
        print("=" * 60)
        
        # Download price data using API
        print("🔄 Fiyat verisi çekiliyor...")
        df = api.download(fund_code)
        
        if df.empty:
            print(f"❌ {fund_code} fonu için fiyat verisi bulunamadı.")
            return False
        
        print(f"✅ {len(df)} adet fiyat verisi alındı.")
        
        # Calculate statistics if requested
        if show_stats:
            print("🔄 Finansal metrikler hesaplanıyor...")
            try:
                stats = api.get_statistics(df, fund_code)
                display_fund_stats(fund_code, stats)
                
                # Get additional data (asset allocation, benchmark)
                try:
                    additional_data = api.get_additional_data(fund_code)
                    if additional_data and (additional_data.get('asset_allocation') or additional_data.get('benchmark_returns')):
                        display_additional_data(fund_code, additional_data)
                except Exception as e:
                    logger.warning(f"Additional data could not be retrieved: {e}")
                
                # Save to file if requested
                if output_file:
                    save_results_to_file(stats, output_file, output_format)
                
            except Exception as e:
                print(f"❌ İstatistik hesaplama hatası: {e}")
                return False
        
        # Show chart if requested
        if show_chart:
            print("🔄 Grafik hazırlanıyor...")
            try:
                api.plot_price_chart(df, fund_code, show=True)
                print("✅ Grafik gösterildi.")
            except Exception as e:
                print(f"❌ Grafik gösterme hatası: {e}")
                return False
        
        print(f"\n✅ {fund_code} fonu analizi tamamlandı!")
        return True
        
    except ScrapingError as e:
        print(f"❌ Veri çekme hatası: {e}")
        return False
    except TefasError as e:
        print(f"❌ TEFAS hatası: {e}")
        return False
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        logger.error(f"Unexpected error analyzing {fund_code}: {e}")
        return False


def compare_funds(fund_codes: list, show_chart: bool = True) -> bool:
    """
    Compare multiple funds using the unified API.
    
    Args:
        fund_codes (list): List of fund codes to compare
        show_chart (bool): Whether to display comparison chart
    
    Returns:
        bool: True if comparison was successful, False otherwise
    """
    try:
        print(f"\n🔄 {len(fund_codes)} fon karşılaştırılıyor: {', '.join(fund_codes)}")
        print("=" * 60)
        
        # Download data for all funds
        fund_data = {}
        successful_funds = []
        
        for fund_code in fund_codes:
            try:
                print(f"🔄 {fund_code} verisi çekiliyor...")
                fund_code_clean = clean_fund_code(fund_code)
                df = api.download(fund_code_clean)
                
                if not df.empty:
                    fund_data[fund_code_clean] = df
                    successful_funds.append(fund_code_clean)
                    print(f"✅ {fund_code_clean}: {len(df)} veri noktası")
                else:
                    print(f"❌ {fund_code_clean}: Veri bulunamadı")
                    
            except Exception as e:
                print(f"❌ {fund_code}: Hata - {e}")
                continue
        
        if len(successful_funds) < 2:
            print("❌ Karşılaştırma için en az 2 fonun verisi gerekli!")
            return False
        
        # Display basic comparison stats
        print(f"\n📊 {len(successful_funds)} FON KARŞILAŞTIRMASI")
        print("=" * 60)
        
        for fund_code, df in fund_data.items():
            try:
                stats = api.get_statistics(df, fund_code)
                print(f"\n💼 {fund_code}:")
                print(f"   📈 Toplam Getiri: %{stats['Toplam_Getiri_%']:.2f}")
                print(f"   📅 CAGR: %{stats['CAGR_%']:.2f}")
                print(f"   ⚡ Volatilite: %{stats['Volatilite_%']:.2f}")
                print(f"   📊 Sharpe: {stats['Sharpe_Ratio']:.3f}")
                print(f"   📋 Veri: {stats['Veri_Sayisi']} gün")
            except Exception as e:
                print(f"   ❌ İstatistik hesaplanamadı: {e}")
        
        # Show comparison chart if requested
        if show_chart and len(fund_data) >= 2:
            print("\n🔄 Karşılaştırma grafiği hazırlanıyor...")
            try:
                api.plot_comparison(fund_data, show=True)
                print("✅ Karşılaştırma grafiği gösterildi.")
            except Exception as e:
                print(f"❌ Grafik gösterme hatası: {e}")
                return False
        
        print(f"\n✅ {len(successful_funds)} fon karşılaştırması tamamlandı!")
        return True
        
    except Exception as e:
        print(f"❌ Karşılaştırma hatası: {e}")
        logger.error(f"Comparison error: {e}")
        return False


def list_popular_funds() -> None:
    """List popular TEFAS funds."""
    print("\n📋 Popüler TEFAS Fonları:")
    print("=" * 40)
    
    popular_funds = get_popular_funds()
    for code, name in popular_funds.items():
        print(f"  • {code} - {name}")
    
    print("\n💡 Kullanım örnekleri:")
    print("  python -m tefas_analyzer.cli CPU --stats")
    print("  python -m tefas_analyzer.cli CPU --chart")
    print("  python -m tefas_analyzer.cli CPU --all")
    print("  python -m tefas_analyzer.cli CPU AAK --compare")
    print("=" * 40)


def main() -> None:
    """Main CLI entry point with yfinance-like interface."""
    parser = argparse.ArgumentParser(
        description='TEFAS Fund Analyzer - yfinance-like interface for Turkish mutual funds',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 Examples:
  python -m tefas_analyzer.cli CPU --stats              # Show statistics only
  python -m tefas_analyzer.cli CPU --chart              # Show chart only  
  python -m tefas_analyzer.cli CPU --all                # Show everything
  python -m tefas_analyzer.cli CPU --output results.json
  python -m tefas_analyzer.cli CPU AAK --compare        # Compare funds
  python -m tefas_analyzer.cli --list                   # List popular funds

🚀 Quick analysis (like yfinance):
  python -m tefas_analyzer.cli CPU                      # Default: stats only
        """
    )
    
    # Positional arguments for fund codes (multiple allowed for comparison)
    parser.add_argument(
        'fund_codes',
        nargs='*',
        help='Fund code(s) to analyze (e.g., CPU, AAK, AFA). Multiple codes for comparison.'
    )
    
    # Action options
    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help='Display financial statistics (default)'
    )
    
    parser.add_argument(
        '--chart', '-c',
        action='store_true',
        help='Display price chart'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Display both statistics and chart'
    )
    
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare multiple funds (requires 2+ fund codes)'
    )
    
    # Output options
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file path for results'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'csv'],
        default='json',
        help='Output format (default: json)'
    )
    
    # Utility options
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List popular TEFAS funds'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Merkezi logging konfigürasyonunu ayarla
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)
    
    # Handle list popular funds
    if args.list:
        list_popular_funds()
        return
    
    # Validate fund codes
    if not args.fund_codes:
        print("❌ Fon kodu belirtilmedi!")
        print("💡 Kullanım: python -m tefas_analyzer.cli <FON_KODU> [SEÇENEKLER]")
        print("💡 Popüler fonları görmek için: python -m tefas_analyzer.cli --list")
        print("💡 Yardım için: python -m tefas_analyzer.cli --help")
        sys.exit(1)
    
    # Handle comparison mode
    if args.compare:
        if len(args.fund_codes) < 2:
            print("❌ Karşılaştırma için en az 2 fon kodu gerekli!")
            print("💡 Örnek: python -m tefas_analyzer.cli CPU AAK --compare")
            sys.exit(1)
        
        # Welcome message for comparison
        print("🚀 TEFAS Fon Karşılaştırma Aracı")
        print("=" * 60)
        print("⚠️  Bu araç Selenium WebDriver kullanır.")
        print("⚠️  Chrome browser ve internet bağlantısı gereklidir.")
        print("=" * 60)
        
        # Compare funds
        try:
            success = compare_funds(args.fund_codes, show_chart=True)
            
            if success:
                print("\n💡 Karşılaştırma tamamlandı!")
            else:
                print("\n❌ Karşılaştırma başarısız oldu!")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n\n❌ Program kullanıcı tarafından iptal edildi.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Kritik hata: {e}")
            logger.error(f"Critical error: {e}")
            sys.exit(1)
        
        return
    
    # Single fund analysis
    if len(args.fund_codes) > 1:
        print("⚠️  Tek fon analizi için sadece bir fon kodu belirtin.")
        print("💡 Çoklu fon karşılaştırması için --compare kullanın.")
        sys.exit(1)
    
    fund_code = args.fund_codes[0]
    
    # Determine what to show
    show_chart = args.chart or args.all
    show_stats = args.stats or args.all
    
    # Default to stats if nothing specified
    if not (args.chart or args.stats or args.all):
        show_stats = True
    
    # Welcome message
    print("🚀 TEFAS Fon Analiz Aracı")
    print("=" * 60)
    print("⚠️  Bu araç Selenium WebDriver kullanır.")
    print("⚠️  Chrome browser ve internet bağlantısı gereklidir.")
    print("=" * 60)
    
    # Analyze fund
    try:
        success = analyze_fund(
            fund_code=fund_code,
            show_chart=show_chart,
            show_stats=show_stats,
            output_file=args.output,
            output_format=args.format
        )
        
        if success:
            print("\n💡 Analiz tamamlandı!")
            if not show_chart:
                print("💡 Grafik görmek için --chart veya --all parametresini kullanın.")
        else:
            print("\n❌ Analiz başarısız oldu!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n❌ Program kullanıcı tarafından iptal edildi.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Kritik hata: {e}")
        logger.error(f"Critical error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
