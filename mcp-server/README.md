# MCP Server untuk AlatBantuTrading

Wrapper Model Context Protocol (MCP) lokal untuk menjembatani **AGY CLI / Gemini CLI / AI Assistant** dengan aplikasi web pasar saham existing (**AlatBantuTrading**).

## 1. Arsitektur Sistem

```text
AGY CLI / Gemini CLI
        ↓
    MCP Server (mcp-server/server.py)
        ↓  (JSON-RPC 2.0 via Stdio)
 HTTP GET / POST / DELETE
        ↓
 localhost Web API (http://127.0.0.1:5000)
        ↓
 Script & Web App Existing (app.py)
        ↓
      Result
        ↓
    MCP Server
        ↓
 AGY CLI / Gemini CLI
```

### Jaminan Keamanan & Non-Invasif
- **Zero modification**: Tidak ada file script atau web interface existing yang diubah atau dihapus.
- **Independent process**: Web interface dan script existing tetap dapat berjalan normal meskipun MCP Server dimatikan atau tidak digunakan.
- **No hardcoded credentials**: MCP Server murni bertindak sebagai HTTP client ke localhost. Token atau API key dikelola secara independen oleh script existing (`stockbit_token.txt`, `gemini_key.txt`).

---

## 2. Daftar MCP Tools (20 Tools)

| Nama MCP Tool | HTTP Method | Endpoint Localhost | Parameter | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `get_watchlist` | GET | `/api/watchlist` | - | Ambil daftar emiten pada watchlist realtime (harga, perubahan) dari akun Stockbit atau fallback. |
| `get_stockbit_status` | GET | `/api/stockbit/status` | - | Periksa status konektivitas akun Stockbit pengguna dan profil akun. |
| `get_stockbit_orderbook` | GET | `/api/stockbit/orderbook` | `symbol` (str, req) | Ambil antrean Orderbook (kedalaman Bid/Offer, volume per baris harga, total volume, ARA/ARB). |
| `get_stockbit_keystats` | GET | `/api/stockbit/keystats` | `symbol` (str, req) | Ambil rasio fundamental (PER, PBV, EPS, ROE, Dividen) & return historis dari Stockbit. |
| `get_stockbit_stream` | GET | `/api/stockbit/stream` | `symbol` (str, req), `limit` (int, opt) | Ambil postingan diskusi komunitas dan sentimen pasar Stockbit terbaru. |
| `get_stockbit_portfolio` | GET | `/api/stockbit/portfolio` | - | Ambil data portofolio & aset Stockbit (cash balance, nilai pasar, PnL, holdings). |
| `get_stock_price` | GET | `/api/price/<symbol>` | `symbol` (str, req) | Ambil harga pasar cepat (last price, perubahan harga, mata uang). |
| `run_stock_analysis` | POST | `/api/analyze` | `symbol` (str, req) | Jalankan pipeline analisis lengkap (pasar realtime, orderbook, Gemini AI, indikator chart). |
| `get_saved_analysis` | GET | `/api/analysis/<symbol>` | `symbol` (str, req) | Ambil hasil analisis terakhir yang sudah tersimpan di database tanpa re-analisis berat. |
| `refresh_stock_analysis`| POST | `/api/refresh_analysis` | `symbol` (str, req) | Perbarui dan jalankan ulang analisis lengkap saham untuk evaluasi AI terkini. |
| `list_chat_history` | GET | `/api/history/list` | - | Ambil daftar seluruh emiten yang memiliki riwayat sesi chat / analisis di database. |
| `get_chat_history_detail`| GET | `/api/history/get/<symbol>` | `symbol` (str, req) | Ambil riwayat percakapan chat dan data analisis tersimpan untuk emiten tertentu. |
| `sync_chat_session` | POST | `/api/chat/sync` | `symbol` (str, req) | Sinkronkan konteks sesi chat saham tertentu atau 'GENERAL' dengan data pasar terbaru. |
| `clear_chat_history` | POST | `/api/chat/clear` | `symbol` (str, req) | Hapus riwayat chat simbol saham tertentu dari database. |
| `send_chat_message` | POST | `/api/chat` | `symbol` (str, opt), `message` (str, req) | Kirim pesan pertanyaan ke chatbot AI pasar saham dan kembalikan jawaban lengkap (menangani SSE). |
| `get_news_archives` | GET | `/api/news_archive/<symbol>` | `symbol` (str, req) | Ambil daftar tautan berita yang telah diarsipkan untuk kode saham tertentu. |
| `add_news_archive` | POST | `/api/news_archive` | `symbol` (str, req), `url` (str, req), `title` (str, opt) | Simpan tautan URL berita penting ke database arsip lokal. |
| `delete_news_archive` | DELETE | `/api/news_archive/<archive_id>` | `archive_id` (int, req) | Hapus item arsip berita berdasarkan ID. |
| `scrape_latest_news` | POST | `/api/refresh_news` | `symbol` (str, req) | Lakukan pencarian dan scraping berita online terkini khusus emiten saham tertentu. |
| `get_debug_last_analysis`| GET | `/debug/last_analysis/<symbol>` | `symbol` (str, req) | Ambil file JSON mentah dari `data/result/<symbol>.json`. |

---

## 3. Konfigurasi AGY CLI / Gemini CLI

Tambahkan konfigurasi berikut ke file **`mcp_config.json`** di root workspace atau secara global di **`~/.gemini/config/mcp_config.json`**:

```json
{
  "mcpServers": {
    "alatbantu-trading": {
      "command": "python",
      "args": [
        "C:/Users/aminm/AlatBantuTrading/mcp-server/server.py"
      ],
      "env": {
        "WEB_API_URL": "http://127.0.0.1:5000"
      }
    }
  }
}
```

*Catatan: Pastikan `python` mengarah ke executable Python yang diinginkan jika menggunakan virtual environment tertentu.*

---

## 4. Cara Menjalankan

### Menjalankan Web App Existing
```bash
# Dari root project AlatBantuTrading:
python app.py
```
Aplikasi web akan aktif di `http://127.0.0.1:5000/`.

### Menjalankan MCP Server
MCP Server dijalankan otomatis oleh AGY CLI / Gemini CLI melalui stdio JSON-RPC. Jika ingin menguji secara langsung di terminal:
```bash
python mcp-server/server.py
```

---

## 5. Cara Menjalankan Pengujian

Tersedia dua script pengujian bawaan di dalam folder `mcp-server/`:

1. **Pengujian Protokol MCP Standar (JSON-RPC stdio)**:
   ```bash
   python mcp-server/test_mcp.py
   ```
   *Menguji handshake `initialize`, notifikasi `notifications/initialized`, `ping`, listing `tools/list`, dan pemanggilan tool.*

2. **Pengujian Fungsional 20 MCP Tools (End-to-End)**:
   ```bash
   python mcp-server/run_verify.py
   ```
   *Menguji seluruh 20 tools ke endpoint localhost HTTP GET/POST/DELETE dan menangani SSE streaming.*
