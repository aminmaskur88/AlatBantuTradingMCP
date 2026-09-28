#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-end test untuk MCP Server dengan mock server localhost:5000.
Menguji bahwa MCP tool berhasil melakukan HTTP GET, POST, DELETE ke localhost
dan mengembalikan hasil ke AI secara transparan.
"""

import sys
import os
import json
import time
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class MockAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Heningkan log default agar output bersih

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>AI Stock Analyzer Pro</body></html>")
        elif self.path == "/api/watchlist":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = [{"ticker": "BBCA", "price": 10200, "change": 150, "change_pct": 1.49}]
            self.wfile.write(json.dumps(data).encode("utf-8"))
        elif self.path.startswith("/api/stockbit/status"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {"connected": True, "username": "trader_pro", "id": 12345}
            self.wfile.write(json.dumps(data).encode("utf-8"))
        elif self.path.startswith("/api/stockbit/orderbook"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "success": True,
                "symbol": "BBCA",
                "data": [
                    {"bid_price": 10175, "bid_volume": 2500, "offer_price": 10200, "offer_volume": 1800}
                ]
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        elif self.path.startswith("/api/price/"):
            symbol = self.path.split("/")[-1]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {"price": 10200, "change": 150, "currency": "IDR"}
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8")
        try:
            body_json = json.loads(post_body)
        except Exception:
            body_json = {}

        if self.path == "/api/analyze":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            symbol = body_json.get("symbol", "BBCA")
            data = {
                "timestamp": "2026-09-28T07:15:00",
                "data": {"symbol": symbol, "price": 10200, "market_trend": "BULLISH"},
                "ai_result": "Analisis teknikal menunjukkan tren akumulasi kuat."
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        elif self.path == "/api/chat":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            msg = f"data: {json.dumps({'status': 'Sedang menganalisa...'})}\n\n"
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()
            reply = f"Saham {body_json.get('symbol', 'BBCA')} berada dalam kondisi tren naik yang solid."
            done_msg = f"data: {json.dumps({'reply': reply, 'done': True})}\n\n"
            self.wfile.write(done_msg.encode("utf-8"))
            self.wfile.flush()
        elif self.path == "/api/chat/sync":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

def run():
    print("==========================================================")
    print(" MENJALANKAN TEST END-TO-END (MCP -> LOCALHOST HTTP -> MCP)")
    print("==========================================================")

    # 1. Jalankan Mock Server di localhost:5000
    server = HTTPServer(("127.0.0.1", 5000), MockAPIHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("[1] Mock Web Server aktif di http://127.0.0.1:5000")

    time.sleep(0.5)

    # 2. Jalankan MCP Server process
    server_script = os.path.join(os.path.dirname(__file__), "server.py")
    proc = subprocess.Popen(
        [sys.executable, server_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )

    def send_rpc(msg):
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        return json.loads(line) if line else None

    # Init
    send_rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    send_rpc({"jsonrpc": "2.0", "method": "notifications/initialized"})

    # Test Tool 1: get_watchlist
    print("[2] Menguji MCP tool 'get_watchlist'...")
    res1 = send_rpc({"jsonrpc": "2.0", "id": 10, "method": "tools/call", "params": {"name": "get_watchlist", "arguments": {}}})
    data1 = json.loads(res1["result"]["content"][0]["text"])
    assert data1["success"] is True
    print(f" -> Respon sukses: {data1['data']}")

    # Test Tool 2: get_stockbit_orderbook
    print("[3] Menguji MCP tool 'get_stockbit_orderbook' (symbol: BBCA)...")
    res2 = send_rpc({"jsonrpc": "2.0", "id": 11, "method": "tools/call", "params": {"name": "get_stockbit_orderbook", "arguments": {"symbol": "BBCA"}}})
    data2 = json.loads(res2["result"]["content"][0]["text"])
    assert data2["success"] is True
    print(f" -> Respon sukses: {data2['data']['data']}")

    # Test Tool 3: get_stock_price
    print("[4] Menguji MCP tool 'get_stock_price' (symbol: BBCA)...")
    res3 = send_rpc({"jsonrpc": "2.0", "id": 12, "method": "tools/call", "params": {"name": "get_stock_price", "arguments": {"symbol": "BBCA"}}})
    data3 = json.loads(res3["result"]["content"][0]["text"])
    assert data3["success"] is True
    print(f" -> Respon sukses: {data3['data']}")

    # Test Tool 4: run_stock_analysis (POST)
    print("[5] Menguji MCP tool 'run_stock_analysis' (POST /api/analyze)...")
    res4 = send_rpc({"jsonrpc": "2.0", "id": 13, "method": "tools/call", "params": {"name": "run_stock_analysis", "arguments": {"symbol": "BBCA"}}})
    data4 = json.loads(res4["result"]["content"][0]["text"])
    assert data4["success"] is True
    print(f" -> Respon sukses: AI Result = {data4['data']['ai_result']}")

    # Test Tool 5: send_chat_message (SSE stream handling)
    print("[6] Menguji MCP tool 'send_chat_message' (SSE stream /api/chat)...")
    res5 = send_rpc({"jsonrpc": "2.0", "id": 14, "method": "tools/call", "params": {"name": "send_chat_message", "arguments": {"symbol": "BBCA", "message": "Bagaimana prospek hari ini?"}}})
    data5 = json.loads(res5["result"]["content"][0]["text"])
    assert data5["success"] is True
    print(f" -> Respon sukses: {data5['reply']}")

    # Selesai
    proc.stdin.close()
    proc.terminate()
    proc.wait()
    server.shutdown()
    server.server_close()

    print("\n[VERIFIKASI BERHASIL] Seluruh komunikasi MCP -> localhost:5000 terbukti berfungsi sempurna!")

if __name__ == "__main__":
    run()
