import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import date, timedelta

def parse_harga(harga_str):
    after_rp = harga_str.split('Rp')[-1].strip()
    match = re.search(r'(\d{1,3}(?:\.\d{3})+)', after_rp)
    if match:
        return int(match.group(1).replace('.', ''))
    match2 = re.search(r'(\d+)', after_rp)
    return int(match2.group(1)) if match2 else 0

def fetch_kota_malang():
    print("Fetching Kota Malang...")
    try:
        r = requests.get("https://sembako.malangkota.go.id", 
            headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
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

def fetch_sp2kp(kode_kab_kota, kode_provinsi, nama_wilayah):
    print(f"Fetching SP2KP {nama_wilayah}...")
    try:
        today_iso = date.today().isoformat()
        yesterday_iso = (date.today() - timedelta(days=1)).isoformat()
        
        r = requests.post(
            "https://api-sp2kp.kemendag.go.id/report/api/average-price/generate-perbandingan-harga",
            data={
                "tanggal": today_iso,
                "tanggal_pembanding": yesterday_iso,
                "kode_provinsi": kode_provinsi,
                "kode_kab_kota": kode_kab_kota
            },
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Origin': 'https://sp2kp.kemendag.go.id',
                'Referer': 'https://sp2kp.kemendag.go.id/'
            },
            timeout=15
        )
        data = r.json()
        items = data.get('data', [])
        
        hasil = {}
        for item in items:
            nama = item.get('variant_nama', '')
            harga = item.get('harga', 0) or item.get('harga_pembanding', 0)
            harga_lama = item.get('harga_pembanding', 0)
            if nama and harga:
                hasil[nama] = {
                    "harga": harga,
                    "harga_lama": harga_lama,
                    "satuan": item.get('satuan_display', 'kg'),
                    "tanggal": today_iso
                }
        print(f"SP2KP {nama_wilayah}: {len(hasil)} komoditas")
        return hasil
    except Exception as e:
        print(f"Error SP2KP {nama_wilayah}: {e}")
        return {}

def fetch_pihps_nasional():
    print("Fetching PIHPS via SP2KP Nasional...")
    try:
        today_iso = date.today().isoformat()
        yesterday_iso = (date.today() - timedelta(days=1)).isoformat()
        
        r = requests.post(
            "https://api-sp2kp.kemendag.go.id/report/api/average-price/generate-perbandingan-harga",
            data={
                "tanggal": today_iso,
                "tanggal_pembanding": yesterday_iso,
                "kode_provinsi": "35",
                "kode_kab_kota": ""
            },
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Origin': 'https://sp2kp.kemendag.go.id',
                'Referer': 'https://sp2kp.kemendag.go.id/'
            },
            timeout=15
        )
        data = r.json()
        items = data.get('data', [])
        
        hasil = {}
        for item in items:
            nama = item.get('variant_nama', '')
            harga = item.get('harga', 0) or item.get('harga_pembanding', 0)
            harga_lama = item.get('harga_pembanding', 0)
            if nama and harga:
                hasil[nama] = {
                    "harga": harga,
                    "harga_lama": harga_lama,
                    "satuan": item.get('satuan_display', 'kg'),
                    "tanggal": today_iso
                }
        print(f"SP2KP Nasional: {len(hasil)} komoditas")
        return hasil
    except Exception as e:
        print(f"Error SP2KP Nasional: {e}")
        return {}

# Buat folder data
os.makedirs('data', exist_ok=True)

# Fetch semua
kota_malang = fetch_kota_malang()
kota_batu = fetch_sp2kp("3579", "35", "Kota Batu")
pihps = fetch_pihps_nasional()

# Simpan ke JSON
with open('data/kota_malang.json', 'w') as f:
    json.dump({"updated": date.today().isoformat(), "data": kota_malang}, f, ensure_ascii=False, indent=2)

with open('data/kota_batu.json', 'w') as f:
    json.dump({"updated": date.today().isoformat(), "data": kota_batu}, f, ensure_ascii=False, indent=2)

with open('data/pihps_nasional.json', 'w') as f:
    json.dump({"updated": date.today().isoformat(), "data": pihps}, f, ensure_ascii=False, indent=2)

print("Selesai!")
