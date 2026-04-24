import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import date

def parse_harga(harga_str):
    """Parse harga dengan deteksi pola titik ribuan"""
    after_rp = harga_str.split('Rp')[-1].strip()
    # Cari pola harga: angka dengan titik ribuan (contoh: 43.000, 126.800, 13.000)
    match = re.search(r'(\d{1,3}(?:\.\d{3})+)', after_rp)
    if match:
        return int(match.group(1).replace('.', ''))
    # Fallback: angka biasa tanpa titik
    match2 = re.search(r'(\d+)', after_rp)
    return int(match2.group(1)) if match2 else 0

def fetch_kota_malang():
    print("Fetching Kota Malang...")
    try:
        r = requests.get("https://sembako.malangkota.go.id", 
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        hasil = {}
        for item in soup.select('li.products'):
            nama = item.select_one('.judul')
            harga = item.select_one('.price_now')
            if nama and harga:
                nama_str = nama.text.strip()
                harga_str = harga.text.strip()
                harga_num = parse_harga(harga_str)
                hasil[nama_str] = {
                    "harga": harga_num,
                    "harga_raw": harga_str,
                    "tanggal": date.today().isoformat()
                }
        print(f"Kota Malang: {len(hasil)} komoditas")
        return hasil
    except Exception as e:
        print(f"Error Kota Malang: {e}")
        return {}

def fetch_pihps_nasional():
    print("Fetching PIHPS Nasional...")
    try:
        from datetime import date
        import urllib.parse
        today = date.today().strftime("%b %d, %Y")
        today_encoded = urllib.parse.quote(today)
        
        tree_url = "https://www.bi.go.id/hargapangan/WebSite/Home/GetCommoditiesTree"
        r_tree = requests.get(tree_url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.bi.go.id/hargapangan',
        }, timeout=15)
        print(f"Tree response: {r_tree.text[:300]}")
        commodities = r_tree.json()
        print(f"Type: {type(commodities)}, content: {str(commodities)[:200]}")
        return {}
    except Exception as e:
        print(f"Error PIHPS: {e}")
        return {}
# Buat folder data
os.makedirs('data', exist_ok=True)

# Fetch semua
kota_malang = fetch_kota_malang()
pihps = fetch_pihps_nasional()

# Simpan ke JSON
with open('data/kota_malang.json', 'w') as f:
    json.dump({"updated": date.today().isoformat(), "data": kota_malang}, f, ensure_ascii=False, indent=2)

with open('data/pihps_nasional.json', 'w') as f:
    json.dump({"updated": date.today().isoformat(), "data": pihps}, f, ensure_ascii=False, indent=2)

print("Selesai!")
