# 📈 AlatBantuTrading - AI Stock Analyzer Pro & MCP Server

Aplikasi analisis saham cerdas berbasis AI (Google Gemini API) terintegrasi dengan **Stockbit Gateway**, **Yahoo Finance**, **BEI/IDX Data**, serta **Model Context Protocol (MCP)** untuk menghubungkan dashboard analitik dengan asisten AI (Antigravity / Gemini CLI).

---

## ✨ Fitur Utama

- **📊 Data Pasar & Orderbook Real-time**: Mengambil live quote harga, antrean Bid/Offer mendalam (Orderbook), serta rasio fundamental kunci (PE, PBV, ROE, Dividend Yield) via Stockbit Gateway.
- **📰 Deep Reading AI News**: Secara otomatis menelusuri berita pasar modal terkini (Bisnis.com, Kontan, CNBC Indonesia), merangkum sentimen, dan mengekstrak katalis penting.
- **🤖 Multi-Agent AI Analyzer**: Arsitektur multi-agent (Planner, Tool Selector, Executor, Validator) bertenaga Google Gemini untuk menghasilkan analisis komprehensif, target harga (*Entry*, *Target Price*, *Cut Loss*), dan kalkulasi proyeksi valuasi.
- **🖼️ Chart Visualisasi Profesional**: Generator grafik teknikal & performa multi-panel (Matplotlib) yang menghasilkan output PNG & PDF resolusi tinggi.
- **💬 Sesi Chat Interaktif & Database SQLite**: Riwayat percakapan interaktif per emiten yang tersimpan rapi di SQLite (`data/chat.db`).
- **🔌 Standalone MCP Bridge**: Server JSON-RPC 2.0 stdio yang kompatibel dengan protokol MCP standar sehingga LLM Agent dapat memanggil tools analisis langsung dari IDE.

---

## 🚀 Panduan Memulai

### 1. Prasyarat Sistem
- **Python 3.10+**
- Sistem Operasi: Windows 10/11 (disertai skrip launcher 1-klik) atau Linux.

### 2. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Kredensial & Kunci API
Salin file template contoh dan isi kredensial Anda:
```bash
# 1. API Key Gemini (Wajib untuk fitur AI Analysis & Chat)
cp gemini_key.txt.example gemini_key.txt

# 2. Token Stockbit (Opsional/Direkomendasikan untuk live orderbook & keystats)
cp stockbit_token.txt.example stockbit_token.txt
```
> *Catatan: File `gemini_key.txt` dan `stockbit_token.txt` otomatis diabaikan oleh `.gitignore` sehingga aman dan tidak akan ter-push ke repositori publik.*

### 4. Menjalankan Aplikasi
* **Windows (Rekomendasi 1-Click):**
  Klik ganda `start_all_admin.bat` atau jalankan via PowerShell:
  ```powershell
  .\start_all_admin.ps1
  ```
* **CLI Standar:**
  ```bash
  python app.py
  ```
* Buka browser di: **`http://127.0.0.1:5000`**

---

## 📂 Struktur Proyek

```text
AlatBantuTrading/
├── src/                                # Seluruh core modules, business logic & tools
│   ├── __init__.py
│   ├── ai_analyzer.py                  # Orkestrator AI Multi-Agent
│   ├── bing_search_tool.py             # Fallback pencarian web
│   ├── chart_bridge.py                 # Integrasi data ke generator chart
│   ├── enhanced_chart_generator.py     # Engine grafik visualisasi
│   ├── financial_data_processor.py     # Kalkulator rasio & indikator
│   ├── formatter.py                    # Formatter data & utilitas SQLite
│   ├── idx_data_service.py             # Layanan data emiten BEI
│   ├── news_scraper.py                 # Scraper berita pasar modal
│   ├── projection_bridge.py            # Kalkulasi proyeksi fundamental
│   ├── scraper.py                      # Scraper browser & web data
│   ├── stockbit_client.py              # Klien API Stockbit Gateway
│   ├── utils.py                        # Pengelola API Key & logging
│   └── yahoo_finance_tool.py           # Helper data Yahoo Finance
│
├── scripts/                            # Skrip CLI & utilitas
│   └── sync_all_stocks.py              # CLI sync data historis emiten BEI
│
├── tests/                              # Suite pengujian unit & modul
│   ├── __init__.py
│   └── test_imports.py                 # Verifikasi integritas import modul
│
├── mcp-server/                         # Model Context Protocol (MCP) Server
│   ├── README.md                       # Dokumentasi MCP
│   ├── server.py                       # MCP Server stdio JSON-RPC bridge
│   ├── run_verify.py                   # Script verifikasi otomatis MCP
│   ├── test_mcp.py                     # Pengujian protokol MCP
│   └── test_e2e_mock.py                # Mock test interaktif MCP
│
├── templates/                          # Template UI Web (HTML/Alpine.js/Tailwind)
│   └── index.html
│
├── static/                             # Aset statis & chart yang dihasilkan
│   └── charts/
│
├── data/                               # Database lokal & cache JSON (di-ignore Git)
│   ├── chat.db
│   ├── clean/
│   ├── raw/
│   └── result/
│
├── app.py                              # Clean Entry Point Web Server
├── run.bat                             # Simple batch launcher
├── start_all_admin.bat                 # Administrator launcher (Batch)
├── start_all_admin.ps1                 # Administrator launcher (PowerShell)
├── mcp_config.json                     # Konfigurasi integrasi MCP
├── indonesia.csv                       # Data master ticker saham BEI
├── requirements.txt                    # Dependensi paket Python
└── .gitignore                          # Aturan ignore Git komprehensif
```

---

## 🧪 Pengujian & Validasi

Untuk menjalankan pengujian integritas modul dan protokol MCP:
```bash
# Uji import seluruh modul src/
python -m unittest tests/test_imports.py

# Uji protokol MCP Server
python mcp-server/test_mcp.py
```

---

## ⚖️ Disclaimer
Aplikasi ini ditujukan sebagai alat bantu analisis pasar dan **bukan merupakan saran/rekomendasi investasi keuangan formal**. Keputusan transaksi jual/beli saham sepenuhnya merupakan tanggung jawab pengguna.
