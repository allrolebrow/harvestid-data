import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import date

def parse_harga(harga_str):
    """Ambil angka harga saja, abaikan satuan"""
    # Ambil bagian setelah "Rp"
    after_rp = harga_str.split('Rp')[-1].strip()
    # Hapus titik ribuan (titik diikuti 3 digit)
    clean = re.sub(r'\.(\d{3})', r'\1', after_rp)
    # Ambil angka di awal saja (sebelum spasi atau huruf)
    match = re.match(r'^(\d+)', clean.strip())
    return int(match.group(1)) if match else 0

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
        today = date.today().strftime("%d/%m/%Y")
        r = requests.post(
            "https://www.bi.go.id/hargapangan/Home/GetGridData",
            data={
                "tipe": "1",
                "komoditas": "0",
                "provinsi": "0",
                "kota": "0",
                "tanggalMulai": today,
                "tanggalSelesai": today
            },
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://www.bi.go.id/hargapangan',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            timeout=15
        )
        data = r.json()
        hasil = {}
        for item in data.get('data', []):
            hasil[item.get('id', '')] = {
                "nama": item.get('nama', ''),
                "harga": item.get('harga', 0),
                "tanggal": date.today().isoformat()
            }
        print(f"PIHPS Nasional: {len(hasil)} komoditas")
        return hasil
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
