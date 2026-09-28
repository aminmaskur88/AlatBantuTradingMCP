import os
import sys
import csv
import time

# Pastikan folder src/ terdeteksi
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from idx_data_service import IDXDataService

def main():
    service = IDXDataService()
    tickers = []
    
    # Ambil daftar ticker dari indonesia.csv di root project
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "indonesia.csv")
    if not os.path.exists(csv_path):
        csv_path = "indonesia.csv"

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tickers.append(row["ticker"].upper())
    except Exception as e:
        print(f"Error membaca indonesia.csv: {e}")
        return

    print(f"Ditemukan {len(tickers)} saham. Memulai sinkronisasi data ke JSON...")
    
    # Untuk mengetes, kita batasi dulu saham-saham utama (Bluechip) atau 10 pertama
    # Jika ingin semuanya, hapus [:10]
    main_tickers = ["BBCA", "BBRI", "BMRI", "TLKM", "ASII", "BBNI", "UNVR", "ADRO", "GOTO", "AMRT"]
    
    # Gabungkan ticker utama dengan yang lain
    sync_list = list(set(main_tickers + tickers[:20])) 

    success_count = 0
    for ticker in sync_list:
        try:
            print(f"[{success_count+1}/{len(sync_list)}] Sinkronisasi {ticker}...", end="\r")
            res = service.get_historical_data(ticker, period="all", force_update=True)
            if res["success"]:
                success_count += 1
            else:
                print(f"\n{ticker} Gagal: {res.get('error')}")
            
            # Jeda sedikit agar tidak kena blokir Yahoo
            time.sleep(1)
        except Exception as e:
            print(f"\nError pada {ticker}: {e}")

    print(f"\nSelesai! Berhasil sinkronisasi {success_count} saham ke database JSON.")

if __name__ == "__main__":
    main()
