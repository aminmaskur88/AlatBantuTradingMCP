#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifikasi langsung fungsi MCP Server dan adapter HTTP ke localhost.
"""

import sys
import os
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import server MCP
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import execute_tool, MCP_TOOLS

class MockAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"AI Stock Analyzer Pro")
        elif self.path == "/api/watchlist":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps([{"ticker": "BBCA", "price": 10200, "change": 150}]).encode("utf-8"))
        elif self.path.startswith("/api/stockbit/status"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"connected": True, "username": "investor_indo"}).encode("utf-8"))
        elif self.path.startswith("/api/stockbit/orderbook"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "symbol": "BBCA", "data": [{"bid_price": 10175, "bid_volume": 2500}]}).encode("utf-8"))
        elif self.path.startswith("/api/stockbit/keystats"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "symbol": "BBCA", "data": {"PE": 22.5, "PBV": 4.8}}).encode("utf-8"))
        elif self.path.startswith("/api/stockbit/stream"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "symbol": "BBCA", "data": [{"content": "Dividen BBCA mantap"}]}).encode("utf-8"))
        elif self.path.startswith("/api/stockbit/portfolio"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "cash_balance": 15000000, "holdings": []}).encode("utf-8"))
        elif self.path.startswith("/api/price/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"price": 10200, "change": 150, "currency": "IDR"}).encode("utf-8"))
        elif self.path.startswith("/api/analysis/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"symbol": "BBCA", "ai_result": "Akumulasi kuat"}).encode("utf-8"))
        elif self.path.startswith("/api/history/list"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps([{"symbol": "BBCA", "name": "Bank Central Asia"}]).encode("utf-8"))
        elif self.path.startswith("/api/history/get/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"history": [], "analysis": {"symbol": "BBCA"}}).encode("utf-8"))
        elif self.path.startswith("/api/news_archive/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"archives": [{"id": 1, "symbol": "BBCA", "url": "https://kontan.co.id"}]}).encode("utf-8"))
        elif self.path.startswith("/debug/last_analysis/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"debug": "ok", "symbol": "BBCA"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        parsed = json.loads(body) if body else {}

        if self.path == "/api/analyze":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"symbol": parsed.get("symbol"), "status": "analisis berhasil"}).encode("utf-8"))
        elif self.path == "/api/refresh_analysis":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"symbol": parsed.get("symbol"), "refreshed": True}).encode("utf-8"))
        elif self.path == "/api/chat/sync":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
        elif self.path == "/api/chat/clear":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
        elif self.path == "/api/news_archive":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "URL diarsipkan"}).encode("utf-8"))
        elif self.path == "/api/refresh_news":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"news": [{"title": "Laba BBCA meningkat"}]}).encode("utf-8"))
        elif self.path == "/api/chat":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(b'data: {"status": "Menganalisa..."}\n\n')
            self.wfile.flush()
            self.wfile.write(b'data: {"reply": "BBCA menunjukkan tren bullish kuat.", "done": true}\n\n')
            self.wfile.flush()
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        if self.path.startswith("/api/news_archive/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Arsip berhasil dihapus"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def main():
    print("=" * 60)
    print(" VERIFIKASI LENGKAP 20 MCP TOOLS -> LOCALHOST WEB API")
    print("=" * 60)

    server = HTTPServer(("127.0.0.1", 5000), MockAPIHandler)
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()
    print("[OK] Localhost HTTP Server aktif di port 5000")

    success_count = 0
    total_tools = len(MCP_TOOLS)

    test_cases = [
        ("get_watchlist", {}),
        ("get_stockbit_status", {}),
        ("get_stockbit_orderbook", {"symbol": "BBCA"}),
        ("get_stockbit_keystats", {"symbol": "BBCA"}),
        ("get_stockbit_stream", {"symbol": "BBCA", "limit": 5}),
        ("get_stockbit_portfolio", {}),
        ("get_stock_price", {"symbol": "BBCA"}),
        ("run_stock_analysis", {"symbol": "BBCA"}),
        ("get_saved_analysis", {"symbol": "BBCA"}),
        ("refresh_stock_analysis", {"symbol": "BBCA"}),
        ("list_chat_history", {}),
        ("get_chat_history_detail", {"symbol": "BBCA"}),
        ("sync_chat_session", {"symbol": "BBCA"}),
        ("clear_chat_history", {"symbol": "BBCA"}),
        ("send_chat_message", {"symbol": "BBCA", "message": "Bagaimana analisa BBCA?"}),
        ("get_news_archives", {"symbol": "BBCA"}),
        ("add_news_archive", {"symbol": "BBCA", "url": "https://kontan.co.id/news/1", "title": "Berita BBCA"}),
        ("delete_news_archive", {"archive_id": 1}),
        ("scrape_latest_news", {"symbol": "BBCA"}),
        ("get_debug_last_analysis", {"symbol": "BBCA"})
    ]

    for tool_name, args in test_cases:
        res = execute_tool(tool_name, args)
        if res.get("success") is True:
            success_count += 1
            print(f"  [PASS] {tool_name:25} -> {str(res.get('data') or res.get('reply'))[:60]}")
        else:
            print(f"  [FAIL] {tool_name:25} -> {res.get('error')}")

    print("=" * 60)
    print(f" Hasil: {success_count}/{total_tools} MCP Tools Berhasil Diuji!")
    print("=" * 60)

    server.shutdown()
    server.server_close()

if __name__ == "__main__":
    main()
