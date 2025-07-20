# TEFAS Fund Analyzer v0.1.0

Bu Python kütüphanesi, TEFAS (Türkiye Elektronik Fon Alım Satım Platformu) üzerinden fon fiyat verilerini indirmenizi sağlar.
Test Pypi: [tefas-analyzer 0.1.0](https://test.pypi.org/project/tefas-analyzer/0.1.0/)  

> **UYARI:** TEFAS platformu, fonlar için maksimum 5 yıllık geçmiş veriye erişim sağlar. Bu paket ile daha eski veri çekilemez. 
> **YASAL:** Bu kütüphane yalnızca kişisel ve eğitim amaçlı kullanım içindir. Yatırım tavsiyesi değildir. Kullanımdan doğacak yasal sorumluluk tamamen kullanıcıya aittir. TEFAS, Borsa İstanbul veya başka bir kurumla resmi bir bağlantısı yoktur. Verilerdeki gecikme, hata veya eksikliklerden yazar sorumlu tutulamaz.
**UYARI** BU PROJENİN TAMAMI YAPAY ZEKA İLE YAZILMIŞTIR.

---

## Özellikler

- Fon fiyat verilerini kolayca indirir.
- Maksimum 5 yıl geriye kadar veri çekebilirsiniz.
- Temel finansal metrikler: toplam getiri, volatilite, CAGR, Sharpe oranı.
- Hatalı fon kodu ve boş veri yönetimi.
- Python 3.8+ ile uyumlu.

---

## Kurulum

```bash
pip install -i https://test.pypi.org/simple/ tefas-analyzer
```
veya
```bash
git clone https://github.com/lleonee/tefas-analyzer.git
cd tefas-analyzer
pip install -e .
```

---

## Temel Kullanım

```python
import tefas_analyzer as tefas

# Maksimum 5 yıl geriye kadar veri çekebilirsiniz.
df = tefas.download('CPU', start='2020-07-01', end='2023-07-01')
print(df.head())  # Sadece Date index ve Price sütunu

# Finansal istatistikler
stats = tefas.get_statistics(df, 'CPU')
print(stats)
```

---

## Fonksiyonlar

| Fonksiyon | Açıklama | Örnek |
|-----------|----------|-------|
| `tefas.download(fon_kodu, start=None, end=None)` | Fon fiyat verisi indirir (tarih aralığı opsiyonel) | `df = tefas.download('CPU', start='2021-01-01', end='2022-01-01')` |
| `tefas.get_statistics(df, fon_kodu)` | Finansal metrikleri hesaplar (DataFrame: Date index, 'Price' sütunu) | `stats = tefas.get_statistics(df, 'CPU')` |

---

## Örnekler

Daha fazla örnek ve detay için `tefas_analyzer_demo.ipynb` dosyasına bakabilirsiniz.


## Katkı ve İletişim

Her türlü görüş, öneri ve katkı için:  
**GitHub:** [lleonee/tefas-analyzer](https://github.com/lleonee/tefas-analyzer)  
**E-posta:** apaydinleonefe@gmail.com  
**Linkedin** [Leon Efe Apaydın](linkedin.com/in/leonefe)
