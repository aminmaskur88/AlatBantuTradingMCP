import os
import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class StockbitClient:
    """
    Client resmi internal Stockbit (exodus.stockbit.com) untuk menarik data
    Orderbook, Bid/Offer Depth, Watchlist, dan Profil secara real-time.
    """
    def __init__(self, token=None, token_file="stockbit_token.txt"):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.token_file = os.path.join(self.base_dir, token_file)
        self.base_url = "https://exodus.stockbit.com"
        self._last_token_mtime = 0
        self.token = token or self._load_token()
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://stockbit.com",
            "Referer": "https://stockbit.com/",
        }
        if self.token:
            clean_token = self.token.replace("Bearer ", "").strip()
            self.headers["Authorization"] = f"Bearer {clean_token}"

    def _load_token(self):
        """Membaca token dari file lokal."""
        if os.path.exists(self.token_file):
            try:
                self._last_token_mtime = os.path.getmtime(self.token_file)
                with open(self.token_file, "r", encoding="utf-8") as f:
                    token = f.read().strip()
                    if token and not token.startswith("#"):
                        return token
            except Exception as e:
                logging.error(f"Gagal membaca token: {e}")
        return None

    def _check_and_reload_token(self):
        """Cek apakah file token di-update di luar, lalu sinkronkan header Authorization."""
        if os.path.exists(self.token_file):
            try:
                mtime = os.path.getmtime(self.token_file)
                if mtime != getattr(self, '_last_token_mtime', 0):
                    new_token = self._load_token()
                    if new_token:
                        self.token = new_token
                        clean_token = new_token.replace("Bearer ", "").strip()
                        self.headers["Authorization"] = f"Bearer {clean_token}"
                        logging.info("Stockbit Bearer token berhasil disinkronkan dari file.")
            except Exception as e:
                logging.error(f"Gagal reload token: {e}")

    def save_token(self, token):
        """Menyimpan token ke file lokal."""
        clean_token = token.replace("Bearer ", "").strip()
        self.token = clean_token
        self.headers["Authorization"] = f"Bearer {clean_token}"
        try:
            with open(self.token_file, "w", encoding="utf-8") as f:
                f.write(clean_token)
            self._last_token_mtime = os.path.getmtime(self.token_file)
            return True
        except Exception as e:
            logging.error(f"Gagal menyimpan token: {e}")
            return False

    def is_authenticated(self):
        self._check_and_reload_token()
        return bool(self.token and len(self.token) > 20)

    def get_user_profile(self):
        """Mendapatkan profil akun Stockbit pengguna."""
        return self._request_get(f"{self.base_url}/user/profile")

    def get_portfolio(self):
        """Mendapatkan data portofolio & aset pengguna dari Stockbit."""
        # Endpoint resmi portofolio di Stockbit Gateway (exodus.stockbit.com)
        endpoints = [
            f"{self.base_url}/virtualtrading/portfolio",
            f"{self.base_url}/portfolio"
        ]
        for ep in endpoints:
            res = self._request_get(ep)
            if res.get("success"):
                return res
        return res

    def get_portfolio_summary(self):
        """
        Menghasilkan ringkasan aset/portofolio yang dimiliki dalam format terstruktur.
        """
        res = self.get_portfolio()
        if not res.get("success"):
            return {
                "success": False,
                "error": res.get("error", "Gagal mengambil data portofolio dari Stockbit"),
                "holdings": [],
                "total_investment": 0,
                "total_market_value": 0,
                "total_unrealized_pl": 0,
                "total_unrealized_pl_pct": 0,
                "cash_balance": 0
            }
        
        raw_data = res.get("data", {}).get("data", {})
        holdings = []
        
        # Ekstrak data saldo & metrik
        amount_info = raw_data.get("amount", {})
        pl_info = raw_data.get("profit_loss", {})
        
        total_inv = amount_info.get("invested", 0) or raw_data.get("total_investment", 0)
        cash = raw_data.get("trading_balance", 0) or raw_data.get("cash_balance", 0)
        total_val = raw_data.get("equity", 0) or (total_inv + cash)
        total_pl = pl_info.get("unrealized", 0) or raw_data.get("total_unrealized_pnl", 0)
        pl_pct = raw_data.get("gain", 0) or ((total_pl / total_inv * 100) if total_inv else 0)

        # Ekstrak data saham/holdings
        items = raw_data.get("result", []) or raw_data.get("holdings", []) or raw_data.get("stocks", []) or []

        for item in items:
            sym = item.get("symbol") or item.get("ticker") or item.get("stock_symbol", "")
            shares = item.get("shares") or item.get("total_shares", 0) or (item.get("lot", 0) * 100)
            lots = item.get("lot", 0) or (shares // 100 if shares else 0)
            avg_price = item.get("avg_price") or item.get("average_price", 0) or item.get("buy_price", 0)
            last_price = item.get("last_price") or item.get("current_price", 0) or item.get("price", 0)
            market_val = item.get("market_value") or (shares * last_price if last_price else 0)
            pl = item.get("unrealized_pnl") or item.get("unrealized_pl", 0) or (market_val - (shares * avg_price) if avg_price else 0)
            pl_p = item.get("unrealized_pnl_pct") or item.get("unrealized_pl_pct", 0) or ((pl / (shares * avg_price) * 100) if (shares and avg_price) else 0)

            holdings.append({
                "symbol": sym.upper(),
                "lot": lots,
                "shares": shares,
                "avg_price": avg_price,
                "last_price": last_price,
                "market_value": market_val,
                "unrealized_pl": pl,
                "unrealized_pl_pct": round(pl_p, 2)
            })

        return {
            "success": True,
            "cash_balance": cash,
            "total_investment": total_inv,
            "total_market_value": total_val,
            "total_unrealized_pl": total_pl,
            "total_unrealized_pl_pct": round(pl_pct, 2),
            "holdings": holdings
        }

    def get_watchlists(self):
        """Mendapatkan daftar watchlist pengguna dari Stockbit."""
        return self._request_get(f"{self.base_url}/watchlist")

    def get_watchlist_stocks(self, watchlist_id):
        """Mengambil daftar emiten/saham dalam watchlist tertentu berdasarkan ID."""
        return self._request_get(f"{self.base_url}/watchlist/{watchlist_id}", params={"limit": 100})

    def get_all_stockbit_watchlist_symbols(self):
        """
        Menarik seluruh simbol saham dari SEMUA watchlist akun Stockbit pengguna.
        Mengembalikan list saham unik dan data realtimenya langsung dari Stockbit.
        """
        wl_res = self.get_watchlists()
        if not wl_res.get("success"):
            return []
        
        watchlists = wl_res.get("data", {}).get("data", [])
        all_symbols_data = {}

        for wl in watchlists:
            w_id = wl.get("watchlist_id")
            if not w_id:
                continue
            detail = self.get_watchlist_stocks(w_id)
            if detail.get("success"):
                raw_data = detail.get("data", {}).get("data", {})
                if isinstance(raw_data, dict):
                    items = raw_data.get("result", []) or raw_data.get("data", [])
                elif isinstance(raw_data, list):
                    items = raw_data
                else:
                    items = []
                
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    sym = item.get("symbol")
                    if sym and sym not in all_symbols_data:
                        try:
                            last_p = float(str(item.get("last", 0)).replace(',', ''))
                            prev_p = float(str(item.get("previous", 0)).replace(',', ''))
                            chg = float(str(item.get("change", 0)).replace('+', ''))
                            pct = float(str(item.get("percent", 0)).replace('+', ''))
                        except Exception:
                            last_p, prev_p, chg, pct = 0, 0, 0, 0
                            
                        all_symbols_data[sym] = {
                            "ticker": sym.upper(),
                            "price": last_p,
                            "change": chg,
                            "change_pct": pct,
                            "name": item.get("name", "")
                        }
        
        return list(all_symbols_data.values())

    def get_orderbook(self, symbol):
        """Mengambil data orderbook saham (Bid / Offer depth)."""
        symbol = symbol.upper().replace(".JK", "").replace("$", "")
        # Gunakan API v2 modern dari Stockbit (company-price-feed)
        v2_url = f"{self.base_url}/company-price-feed/v2/orderbook/companies/{symbol}"
        res = self._request_get(v2_url)
        if res.get("success"):
            raw_data = res.get("data", {}).get("data", {})
            bids = raw_data.get("bid", []) or []
            offers = raw_data.get("offer", []) or []
            
            # Format ke list ladder per level harga (kompatibel langsung dengan frontend & AI)
            max_len = max(len(bids), len(offers))
            ladder = []
            for i in range(max_len):
                b = bids[i] if i < len(bids) else {}
                o = offers[i] if i < len(offers) else {}
                ladder.append({
                    "bid_price": int(b.get("price", 0) or 0),
                    "bid_volume": int(b.get("volume", 0) or 0) // 100,  # Konversi shares ke lot
                    "bid_que": int(b.get("que_num", 0) or 0),
                    "offer_price": int(o.get("price", 0) or 0),
                    "offer_volume": int(o.get("volume", 0) or 0) // 100,  # Konversi shares ke lot
                    "offer_que": int(o.get("que_num", 0) or 0)
                })
            
            return {
                "success": True,
                "data": {
                    "data": ladder,
                    "raw": raw_data,
                    "total_bid_offer": raw_data.get("total_bid_offer", {}),
                    "lastprice": raw_data.get("lastprice"),
                    "average": raw_data.get("average"),
                    "ara": raw_data.get("ara"),
                    "arb": raw_data.get("arb"),
                    "change": raw_data.get("change"),
                    "percentage_change": raw_data.get("percentage_change")
                }
            }
        
        # Fallback ke endpoint legacy jika v2 gagal
        return self._request_get(f"{self.base_url}/orderbook", params={"symbol": symbol})

    def get_keystats(self, symbol):
        """Mengambil data Key Financials & Ratio resmi dari Stockbit."""
        symbol = symbol.upper().replace(".JK", "").replace("$", "")
        return self._request_get(f"{self.base_url}/keystats/{symbol}")

    def get_fundamental_summary(self, symbol):
        """
        Mengambil ringkasan data fundamental terkini (EPS, PER, PBV, Dividen, Return Historis 1Y, 52W High/Low) dari Stockbit.
        """
        symbol = symbol.upper().replace(".JK", "").replace("$", "")
        res = self.get_keystats(symbol)
        if not res.get("success"):
            return None
        
        raw_data = res.get("data", {}).get("data", {})
        keystats_dict = {}
        for grp in raw_data.get("closure_fin_items_results", []):
            for it in grp.get("fin_name_results", []):
                name = it.get("fitem_name")
                val = it.get("fitem_value")
                if name:
                    keystats_dict[name] = val
        return keystats_dict

    def get_stream(self, symbol, limit=10):
        """Mengambil data stream / berita & diskusi emiten terbaru dari komunitas Stockbit."""
        symbol = symbol.upper().replace(".JK", "").replace("$", "")
        return self._request_get(f"{self.base_url}/stream/symbol/{symbol}", params={"limit": limit})

    def get_stockbit_context(self, symbol):
        """
        Menghasilkan teks ringkasan konteks pasar Stockbit untuk diumpankan ke AI Gemini.
        Mencakup Orderbook, Fundamental Terkini, Data Historis Return, dan Sentimen Stream/Diskusi Stockbit.
        """
        symbol = symbol.upper().replace(".JK", "").replace("$", "")
        ob_res = self.get_orderbook(symbol)
        fund_dict = self.get_fundamental_summary(symbol)
        stream_res = self.get_stream(symbol, limit=8)
        
        # Ekstrak Fundamental jika tersedia
        fund_str = ""
        if fund_dict:
            fund_str = (
                f"\n[STOCKBIT FUNDAMENTAL & VALUATION - {symbol}]\n"
                f"- PE Ratio (TTM): {fund_dict.get('Current PE Ratio (TTM)', '-')}\n"
                f"- Forward PE Ratio: {fund_dict.get('Forward PE Ratio', '-')}\n"
                f"- PBV (Price to Book): {fund_dict.get('Current Price to Book Value', '-')}\n"
                f"- EPS (TTM): {fund_dict.get('Current EPS (TTM)', '-')}\n"
                f"- Book Value Per Share: {fund_dict.get('Current Book Value Per Share', '-')}\n"
                f"- ROE (TTM): {fund_dict.get('Return on Equity (TTM)', '-')}\n"
                f"- ROA (TTM): {fund_dict.get('Return on Assets (TTM)', '-')}\n"
                f"- NPM (Net Profit Margin): {fund_dict.get('Net Profit Margin (Quarter)', '-')}\n"
                f"- Dividen Terkini: Rp {fund_dict.get('Dividend', '-')} (TTM: Rp {fund_dict.get('Dividend (TTM)', '-')})\n"
                f"- Dividend Yield: {fund_dict.get('Dividend Yield', '-')}\n"
                f"- Payout Ratio: {fund_dict.get('Payout Ratio', '-')}\n"
                f"- Latest Ex-Date: {fund_dict.get('Latest Dividend Ex-Date', '-')}\n"
                f"[STOCKBIT HISTORICAL PERFORMANCES & 52-WEEK]\n"
                f"- 1 Week Return: {fund_dict.get('1 Week Price Returns', '-')}\n"
                f"- 1 Month Return: {fund_dict.get('1 Month Price Returns', '-')}\n"
                f"- 3 Month Return: {fund_dict.get('3 Month Price Returns', '-')}\n"
                f"- 1 Year Price Return: {fund_dict.get('1 Year Price Returns', '-')}\n"
                f"- 52 Week High: {fund_dict.get('52 Week High', '-')}\n"
                f"- 52 Week Low: {fund_dict.get('52 Week Low', '-')}\n"
            )

        # Ekstrak Sentimen Stream & Berita dari Komunitas Stockbit
        stream_str = ""
        if stream_res.get("success"):
            posts = stream_res.get("data", {}).get("data", [])
            extracted_posts = []
            for p in posts[:6]:
                raw_c = p.get("content", "").replace("\n", " ").strip()
                # Clean non-ascii / emoji safely
                clean_c = raw_c.encode('ascii', 'ignore').decode('ascii')
                author = p.get("username", "Investor")
                likes = p.get("likes_count", 0)
                if clean_c:
                    extracted_posts.append(f"- [@{author} | {likes} likes]: {clean_c[:200]}")
            if extracted_posts:
                stream_str = (
                    f"\n[STOCKBIT STREAM & MARKET SENTIMENT - {symbol}]\n"
                    + "\n".join(extracted_posts) + "\n"
                )

        if not ob_res.get("success"):
            base_status = f"[STOCKBIT LIVE DATA]\nStatus: Orderbook offline ({ob_res.get('error')})."
            return f"{base_status}\n{fund_str}\n{stream_str}".strip()

        raw_data = ob_res.get("data", {}).get("data", [])
        if not raw_data:
            ob_status = (
                f"[STOCKBIT LIVE ORDERBOOK - EMITEN {symbol}]\n"
                f"Status: Terhubung ke Stockbit (Akun Aktif).\n"
                f"Orderbook: Pasar sedang tutup / antrean kosong saat ini.\n"
            )
            return f"{ob_status}\n{fund_str}\n{stream_str}".strip()

        # Jika data orderbook terisi (saat jam bursa aktif)
        bid_total_vol = 0
        offer_total_vol = 0
        bid_list = []
        offer_list = []

        for item in raw_data:
            b_vol = item.get("bid_volume", 0)
            b_price = item.get("bid_price", 0)
            o_vol = item.get("offer_volume", 0)
            o_price = item.get("offer_price", 0)
            
            if b_vol and b_price:
                bid_total_vol += b_vol
                bid_list.append(f"{b_price}: {b_vol} lot")
            if o_vol and o_price:
                offer_total_vol += o_vol
                offer_list.append(f"{o_price}: {o_vol} lot")

        pressure = "NETRAL"
        if bid_total_vol > offer_total_vol * 1.3:
            pressure = "DOMINAN BUY / AKUMULASI (Antrean Bid jauh lebih tebal dibanding Offer)"
        elif offer_total_vol > bid_total_vol * 1.3:
            pressure = "DOMINAN SELL / DISTRIBUSI (Antrean Offer menggunung)"

        context_str = (
            f"[STOCKBIT REALTIME ORDERBOOK - {symbol}]\n"
            f"- Total Volume Bid: {bid_total_vol:,} lot\n"
            f"- Total Volume Offer: {offer_total_vol:,} lot\n"
            f"- Tekanan Pasar: {pressure}\n"
            f"- Antrean Bid Teratas: {', '.join(bid_list[:5]) if bid_list else 'N/A'}\n"
            f"- Antrean Offer Teratas: {', '.join(offer_list[:5]) if offer_list else 'N/A'}\n"
        )
        return f"{context_str}\n{fund_str}\n{stream_str}".strip()

    def _request_get(self, url, params=None):
        if not self.is_authenticated():
            return {
                "success": False,
                "error": "Bearer Token belum diatur di stockbit_token.txt."
            }
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            elif response.status_code == 401:
                return {"success": False, "error": "Token expired atau tidak valid (HTTP 401 Unauthorized)."}
            else:
                return {
                    "success": False, 
                    "status_code": response.status_code, 
                    "raw": response.text[:300]
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Singleton client instance
stockbit_client = StockbitClient()

if __name__ == "__main__":
    import sys
    print("=== Testing Stockbit Client Helper ===")
    sym = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
    ctx = stockbit_client.get_stockbit_context(sym)
    print(ctx)
