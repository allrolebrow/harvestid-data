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
        import urllib.parse, time
        today = date.today().strftime("%b %d, %Y")
        today_encoded = urllib.parse.quote(today)
        
        tree_url = "https://www.bi.go.id/hargapangan/WebSite/Home/GetCommoditiesTree"
        r_tree = requests.get(tree_url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.bi.go.id/hargapangan',
        }, timeout=15)
        tree = r_tree.json().get('data', [])
        
        # Ambil hanya komoditas utama (ParentID = None dan HasCom = 1)
        komoditas_utama = [t for t in tree if t.get('ParentID') is None and t.get('HasCom') == 1]
        print(f"Komoditas utama: {len(komoditas_utama)}")
        
        hasil = {}
        for com in komoditas_utama[:2]:  # Test 2 dulu
            com_id = com['TreeID']
            com_nama = com['TreeName']
            
            url = f"https://www.bi.go.id/hargapangan/WebSite/Home/GetGridData1?tanggal={today_encoded}&commodity={com_id}&priceType=1&isPasokan=1&jenis=1&periode=1&provId=0&_=1234567890"
            r = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Referer': 'https://www.bi.go.id/hargapangan',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8',
                'Cookie': ''
            }, timeout=15)
            print(f"Status: {r.status_code}, Length: {len(r.text)}, Preview: {r.text[:100]}")
            
            items = r.json()
            if isinstance(items, dict):
                items = items.get('data', [])
            
            print(f"{com_nama}: {len(items)} rows")
            if items:
                print(f"Keys: {list(items[0].keys())}")
                print(f"Sample: {items[0]}")
            
            time.sleep(0.3)
        
        print(f"PIHPS Nasional: {len(hasil)} komoditas")
        return hasil
    except Exception as e:
        print(f"Error PIHPS: {e}")
        return {}

def fetch_sp2kp(kode_kab_kota, kode_provinsi, nama_wilayah):
    print(f"Fetching SP2KP {nama_wilayah}...")
    try:
        from datetime import date, timedelta
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        
        r = requests.post(
            "https://api-sp2kp.kemendag.go.id/report/api/average-price/generate-perbandingan-harga",
            json={
                "tanggal": today,
                "tanggal_pembanding": yesterday,
                "kode_provinsi": kode_provinsi,
                "kode_kab_kota": kode_kab_kota
            },
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Content-Type': 'application/json',
                'Origin': 'https://sp2kp.kemendag.go.id',
                'Referer': 'https://sp2kp.kemendag.go.id/'
            },
            timeout=15
        )
        print(f"Status: {r.status_code}, Preview: {r.text[:300]}")
        return r.json()
    except Exception as e:
        print(f"Error SP2KP {nama_wilayah}: {e}")
        return {}

# Test di bagian bawah sebelum simpan JSON
kota_batu = fetch_sp2kp("3579", "35", "Kota Batu")
print(f"Kota Batu keys: {list(kota_batu.keys()) if kota_batu else 'kosong'}")

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
