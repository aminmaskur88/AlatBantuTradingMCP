#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Context Protocol (MCP) Server untuk AlatBantuTrading.
Bertindak sebagai wrapper / bridge independen yang meneruskan request ke web API lokal (Flask).
Script dan web interface existing tidak diubah sama sekali.
"""

import sys
import os
import json
import logging
import urllib.request
import urllib.parse
import urllib.error

# Konfigurasi logging ke stderr agar tidak merusak stdout JSON-RPC
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (MCP-Server) %(message)s"
)

# Konfigurasi URL base web API existing (default: http://127.0.0.1:5000)
BASE_API_URL = os.environ.get("WEB_API_URL", "http://127.0.0.1:5000").rstrip("/")

def send_http_request(method, path, params=None, json_body=None, timeout=60):
    """
    Kirim request HTTP ke web API lokal existing.
    Mendukung GET, POST, DELETE.
    """
    url = f"{BASE_API_URL}{path}"
    if params:
        query_string = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{url}?{query_string}"

    headers = {
        "Accept": "application/json",
        "User-Agent": "AlatBantuTrading-MCP-Wrapper/1.0"
    }

    data_bytes = None
    if json_body is not None:
        headers["Content-Type"] = "application/json"
        data_bytes = json.dumps(json_body).encode("utf-8")

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.status
            content_type = response.headers.get("Content-Type", "")
            raw_body = response.read().decode("utf-8", errors="replace")
            
            try:
                parsed_json = json.loads(raw_body)
                return {
                    "success": 200 <= status_code < 300,
                    "status_code": status_code,
                    "data": parsed_json
                }
            except json.JSONDecodeError:
                return {
                    "success": 200 <= status_code < 300,
                    "status_code": status_code,
                    "data": raw_body
                }
    except urllib.error.HTTPError as e:
        raw_err = e.read().decode("utf-8", errors="replace")
        try:
            parsed_err = json.loads(raw_err)
        except Exception:
            parsed_err = raw_err
        return {
            "success": False,
            "status_code": e.code,
            "error": f"HTTP {e.code}: {parsed_err}"
        }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "status_code": 0,
            "error": (
                f"Koneksi ke web app lokal gagal ({url}). "
                f"Pastikan aplikasi web (app.py) sedang berjalan di port 5000. Alasan: {e.reason}"
            )
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "error": f"Error tak terduga saat memanggil {url}: {str(e)}"
        }

def send_chat_sse(symbol, message, timeout=120):
    """
    Mengirim pesan ke endpoint /api/chat (SSE stream) dan mengumpulkan respon akhir.
    """
    url = f"{BASE_API_URL}/api/chat"
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": "AlatBantuTrading-MCP-Wrapper/1.0"
    }
    payload = {
        "symbol": symbol.strip().upper() if symbol else "GENERAL",
        "message": message
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

    try:
        final_reply = ""
        statuses = []
        with urllib.request.urlopen(req, timeout=timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if line.startswith("data:"):
                    json_str = line[5:].strip()
                    try:
                        chunk = json.loads(json_str)
                        if "status" in chunk:
                            statuses.append(chunk["status"])
                        if "reply" in chunk:
                            final_reply = chunk["reply"]
                        if chunk.get("done"):
                            if "reply" in chunk:
                                final_reply = chunk["reply"]
                            break
                        if "error" in chunk:
                            return {
                                "success": False,
                                "error": chunk["error"],
                                "statuses": statuses
                            }
                    except json.JSONDecodeError:
                        continue
        return {
            "success": True,
            "reply": final_reply or ("\n".join(statuses) if statuses else "Tidak ada respon"),
            "statuses": statuses
        }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"Gagal terhubung ke chat endpoint ({url}): {e.reason}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error chat SSE: {str(e)}"
        }

# Daftar definisi MCP Tools
MCP_TOOLS = [
    {
        "name": "get_watchlist",
        "description": "Mengambil daftar emiten pada watchlist realtime (harga terkini, persentase kenaikan/penurunan dari akun Stockbit atau fallback lokal).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_stockbit_status",
        "description": "Memeriksa status konektivitas akun Stockbit pengguna dan profil akun yang terhubung.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_stockbit_orderbook",
        "description": "Mengambil susunan realtime antrean Orderbook (kedalaman Bid/Offer, volume per baris harga, total volume antrean, batasan ARA/ARB) dari Stockbit Gateway.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA, BBRI, TLKM, ASII, GOTO"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_stockbit_keystats",
        "description": "Mengambil ringkasan rasio fundamental kunci, metrik valuasi (PE, PBV, EPS, ROE, ROA, NPM), dividen, serta return performa historis (1W, 1M, 1Y, 52W High/Low) dari Stockbit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA, BMRI"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_stockbit_stream",
        "description": "Mengambil aliran postingan berita & obrolan diskusi komunitas Stockbit terbaru untuk emiten saham tertentu.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA"
                },
                "limit": {
                    "type": "integer",
                    "description": "Batas jumlah postingan yang diambil (default 15)"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_stockbit_portfolio",
        "description": "Mengambil data portofolio & aset Stockbit pengguna (saldo kas/trading balance, total nilai investasi, total nilai pasar, unrealized PnL, dan rincian kepemilikan saham).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_stock_price",
        "description": "Mengambil data harga pasar cepat (last price, perubahan harga, mata uang) untuk suatu simbol saham.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "run_stock_analysis",
        "description": "Menjalankan pipeline analisis lengkap untuk saham tertentu (mengambil data pasar realtime, orderbook Stockbit, teknikal indikator, analisis AI Gemini, serta data chart). Hasilnya disimpan otomatis ke database lokal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA, TLKM"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_saved_analysis",
        "description": "Mengambil hasil analisis terakhir yang sudah pernah disimpan di database untuk saham tertentu tanpa menjalankan ulang pipeline yang berat.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "refresh_stock_analysis",
        "description": "Memperbarui dan menjalankan ulang analisis lengkap saham tertentu untuk memperoleh data pasar dan evaluasi AI terbaru.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "list_chat_history",
        "description": "Mendapatkan daftar seluruh emiten saham yang memiliki riwayat sesi chat / analisis tersimpan di database lokal.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_chat_history_detail",
        "description": "Mendapatkan detail riwayat percakapan chat dan data analisis tersimpan untuk simbol tertentu (sekaligus memperbarui harga live).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "sync_chat_session",
        "description": "Menyiapkan dan menyinkronkan konteks sesi chat saham tertentu (atau 'GENERAL') dengan data harga pasar terkini ke database sebelum memulai percakapan baru.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI (misal BBCA) atau 'GENERAL'"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "clear_chat_history",
        "description": "Menghapus riwayat percakapan chat untuk suatu simbol saham dari database.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI yang riwayat chat-nya ingin dihapus, misal BBCA"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "send_chat_message",
        "description": "Mengirimkan pesan / pertanyaan ke chatbot AI pasar saham melalui backend lokal dan mengembalikan jawaban analisis AI.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham yang menjadi fokus bahasan (misal BBCA) atau 'GENERAL' untuk pertanyaan umum"
                },
                "message": {
                    "type": "string",
                    "description": "Teks pesan atau pertanyaan yang diajukan ke asisten pasar saham"
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "get_news_archives",
        "description": "Mengambil daftar tautan berita yang telah diarsipkan di database lokal untuk kode saham tertentu.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "add_news_archive",
        "description": "Menyimpan dan mengarsipkan URL berita penting terkait emiten saham ke database lokal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA"
                },
                "url": {
                    "type": "string",
                    "description": "Tautan URL artikel berita lengkap"
                },
                "title": {
                    "type": "string",
                    "description": "Judul artikel berita (opsional)"
                }
            },
            "required": ["symbol", "url"]
        }
    },
    {
        "name": "delete_news_archive",
        "description": "Menghapus data arsip tautan berita berdasarkan ID arsip.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "archive_id": {
                    "type": "integer",
                    "description": "ID numerik arsip yang ingin dihapus"
                }
            },
            "required": ["archive_id"]
        }
    },
    {
        "name": "scrape_latest_news",
        "description": "Melakukan pencarian dan scraping berita online terkini khusus untuk kode saham tertentu.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_debug_last_analysis",
        "description": "Melihat isi file JSON hasil analisis terakhir di data/result/<symbol>.json untuk keperluan inspeksi langsung.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Kode saham BEI, misalnya BBCA"
                }
            },
            "required": ["symbol"]
        }
    }
]

def execute_tool(name, args):
    """
    Mengeksekusi tool yang dipanggil oleh AI dengan meneruskan HTTP request ke localhost.
    """
    args = args or {}
    logging.info(f"Mengeksekusi tool: {name} dengan parameter: {args}")

    if name == "get_watchlist":
        return send_http_request("GET", "/api/watchlist")

    elif name == "get_stockbit_status":
        return send_http_request("GET", "/api/stockbit/status")

    elif name == "get_stockbit_orderbook":
        symbol = args.get("symbol", "").strip()
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("GET", "/api/stockbit/orderbook", params={"symbol": symbol})

    elif name == "get_stockbit_keystats":
        symbol = args.get("symbol", "").strip()
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("GET", "/api/stockbit/keystats", params={"symbol": symbol})

    elif name == "get_stockbit_stream":
        symbol = args.get("symbol", "").strip()
        limit = args.get("limit", 15)
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("GET", "/api/stockbit/stream", params={"symbol": symbol, "limit": limit})

    elif name == "get_stockbit_portfolio":
        return send_http_request("GET", "/api/stockbit/portfolio")

    elif name == "get_stock_price":
        symbol = args.get("symbol", "").strip().upper()
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("GET", f"/api/price/{urllib.parse.quote(symbol)}")

    elif name == "run_stock_analysis":
        symbol = args.get("symbol", "").strip().upper()
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("POST", "/api/analyze", json_body={"symbol": symbol}, timeout=180)

    elif name == "get_saved_analysis":
        symbol = args.get("symbol", "").strip().upper()
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("GET", f"/api/analysis/{urllib.parse.quote(symbol)}")

    elif name == "refresh_stock_analysis":
        symbol = args.get("symbol", "").strip().upper()
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("POST", "/api/refresh_analysis", json_body={"symbol": symbol}, timeout=180)

    elif name == "list_chat_history":
        return send_http_request("GET", "/api/history/list")

    elif name == "get_chat_history_detail":
        symbol = args.get("symbol", "").strip().upper()
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("GET", f"/api/history/get/{urllib.parse.quote(symbol)}")

    elif name == "sync_chat_session":
        symbol = args.get("symbol", "GENERAL").strip().upper()
        return send_http_request("POST", "/api/chat/sync", json_body={"symbol": symbol})

    elif name == "clear_chat_history":
        symbol = args.get("symbol", "").strip().upper()
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("POST", "/api/chat/clear", json_body={"symbol": symbol})

    elif name == "send_chat_message":
        symbol = args.get("symbol", "GENERAL")
        message = args.get("message", "")
        if not message:
            return {"success": False, "error": "Parameter 'message' tidak boleh kosong."}
        return send_chat_sse(symbol, message)

    elif name == "get_news_archives":
        symbol = args.get("symbol", "").strip().upper()
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("GET", f"/api/news_archive/{urllib.parse.quote(symbol)}")

    elif name == "add_news_archive":
        symbol = args.get("symbol", "").strip().upper()
        url = args.get("url", "").strip()
        title = args.get("title", "").strip()
        if not symbol or not url:
            return {"success": False, "error": "Parameter 'symbol' dan 'url' wajib diisi."}
        return send_http_request("POST", "/api/news_archive", json_body={"symbol": symbol, "url": url, "title": title})

    elif name == "delete_news_archive":
        archive_id = args.get("archive_id")
        if archive_id is None:
            return {"success": False, "error": "Parameter 'archive_id' wajib diisi."}
        return send_http_request("DELETE", f"/api/news_archive/{int(archive_id)}")

    elif name == "scrape_latest_news":
        symbol = args.get("symbol", "").strip().upper()
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("POST", "/api/refresh_news", json_body={"symbol": symbol}, timeout=60)

    elif name == "get_debug_last_analysis":
        symbol = args.get("symbol", "").strip().upper()
        if not symbol:
            return {"success": False, "error": "Parameter 'symbol' wajib diisi."}
        return send_http_request("GET", f"/debug/last_analysis/{urllib.parse.quote(symbol)}")

    else:
        return {"success": False, "error": f"Tool '{name}' tidak dikenal."}

def main():
    # Pastikan encoding UTF-8 untuk I/O
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    logging.info(f"MCP Server berjalan, terhubung ke target API: {BASE_API_URL}")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON received: {e}")
                continue

            req_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            # MCP Notifications (tidak memerlukan balasan)
            if req_id is None:
                if method == "notifications/initialized":
                    logging.info("Client MCP initialized notification diterima.")
                continue

            # MCP RPC Methods
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "alatbantu-trading-mcp",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "ping":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {}
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": MCP_TOOLS
                    }
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                tool_result = execute_tool(tool_name, tool_args)
                
                is_error = not tool_result.get("success", False)
                text_content = json.dumps(tool_result, ensure_ascii=False, indent=2)

                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": text_content
                            }
                        ],
                        "isError": is_error
                    }
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found."
                    }
                }

            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()

        except Exception as e:
            logging.error(f"Error pada loop utama MCP: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
