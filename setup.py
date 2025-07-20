from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="tefas-analyzer",
    version="0.1.0",
    author="Leon Efe Apaydın",
    author_email="apaydinleonefe@gmail.com",
    description="yfinance-style Turkish fund analyzer - Professional TEFAS analysis toolkit. Kişisel kullanım içindir, TEFAS'tan veri çeker, yasal sorumluluk kabul edilmez.",
    long_description=long_description + "\n\nNOT: Bu kütüphane TEFAS (Türkiye Elektronik Fon Alım Satım Platformu) web sitesinden veri çeker. Sadece kişisel ve eğitim amaçlı kullanım içindir. Yatırım tavsiyesi değildir. Kullanımdan doğacak yasal sorumluluk tamamen kullanıcıya aittir. TEFAS, Borsa İstanbul veya başka bir kurumla resmi bir bağlantısı yoktur. Verilerdeki gecikme, hata veya eksikliklerden yazar sorumlu tutulamaz.",
    long_description_content_type="text/markdown",
    url="https://github.com/lleonee/tefas-analyzer",
    project_urls={
        "Bug Reports": "https://github.com/lleonee/tefas-analyzer/issues",
        "Source": "https://github.com/lleonee/tefas-analyzer",
        "Documentation": "https://github.com/lleonee/tefas-analyzer#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry", 
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12", 
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="tefas, mutual funds, finance, turkey, yfinance, investment, analysis",
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "build>=0.7.0", 
            "twine>=3.0.0",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tefas=tefas_analyzer.cli:main",
            "tefas-analyzer=tefas_analyzer.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
