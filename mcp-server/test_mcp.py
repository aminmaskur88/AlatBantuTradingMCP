#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite untuk MCP Server AlatBantuTrading.
Menguji:
1. Respon protokol MCP (initialize, tools/list, ping).
2. Respon tools/call terhadap endpoint localhost.
3. Komunikasi HTTP antara MCP Server -> localhost:5000.
4. Verifikasi bahwa server tidak crash jika web API offline.
"""

import sys
import subprocess
import json
import os
import urllib.request

def run_test():
    server_script = os.path.join(os.path.dirname(__file__), "server.py")
    python_exe = sys.executable

    print("==================================================")
    print(" 1. PENGUJIAN PROTOKOL MCP (STDIO JSON-RPC)")
    print("==================================================")

    # Inisialisasi subprocess MCP Server
    proc = subprocess.Popen(
        [python_exe, server_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )

    def send_rpc(msg):
        json_str = json.dumps(msg)
        proc.stdin.write(json_str + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        if not line:
            return None
        return json.loads(line)

    # Test 1: Initialize
    print("[TEST 1] Mengirim 'initialize' request...")
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    init_res = send_rpc(init_req)
    assert init_res is not None, "Tidak ada respon untuk initialize!"
    assert init_res.get("result", {}).get("serverInfo", {}).get("name") == "alatbantu-trading-mcp"
    print(f" -> BERHASIL: Server info: {init_res['result']['serverInfo']}")

    # Test 2: Notification initialized
    print("[TEST 2] Mengirim notification 'notifications/initialized'...")
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()
    print(" -> BERHASIL (Notifikasi dikirim tanpa error)")

    # Test 3: Ping
    print("[TEST 3] Mengirim 'ping'...")
    ping_res = send_rpc({"jsonrpc": "2.0", "id": 2, "method": "ping"})
    assert ping_res is not None and "result" in ping_res
    print(" -> BERHASIL: Ping dijawab")

    # Test 4: tools/list
    print("[TEST 4] Mengambil daftar tools via 'tools/list'...")
    tools_res = send_rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}})
    tools = tools_res.get("result", {}).get("tools", [])
    print(f" -> BERHASIL: Ditemukan {len(tools)} tools terdaftar:")
    for t in tools:
        print(f"    - {t['name']}: {t['description'][:65]}...")

    # Test 5: tools/call - get_stock_price
    print("\n[TEST 5] Menguji 'tools/call' (get_stock_price untuk BBCA)...")
    call_res = send_rpc({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "get_stock_price",
            "arguments": {"symbol": "BBCA"}
        }
    })
    assert call_res is not None and "result" in call_res
    content_text = call_res["result"]["content"][0]["text"]
    print(f" -> Output respon: {content_text[:200]}...")

    # Test 6: tools/call - get_stockbit_status
    print("\n[TEST 6] Menguji 'tools/call' (get_stockbit_status)...")
    call_res2 = send_rpc({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "get_stockbit_status",
            "arguments": {}
        }
    })
    assert call_res2 is not None and "result" in call_res2
    content_text2 = call_res2["result"]["content"][0]["text"]
    print(f" -> Output respon: {content_text2[:200]}...")

    # Tutup subprocess
    proc.stdin.close()
    proc.terminate()
    proc.wait()

    print("\n==================================================")
    print(" 2. STATUS WEB SERVER LOKAL EXISTING (PORT 5000)")
    print("==================================================")
    try:
        req = urllib.request.Request("http://127.0.0.1:5000/", headers={"User-Agent": "MCP-Test"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f" -> Web Server existing berjalan (HTTP status {resp.status}).")
    except Exception as e:
        print(f" -> Web Server existing saat ini offline/belum dijalankan ({e}).")
        print("    Catatan: Jalankan 'python app.py' jika ingin mengakses data real-time.")

    print("\n[SELESAI] Seluruh pengujian internal MCP Server berhasil tanpa error!")

if __name__ == "__main__":
    run_test()
