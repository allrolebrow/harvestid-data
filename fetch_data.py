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

def load_old(filename):
    try:
        with open(f'data/{filename}.json') as f:
            return json.load(f).get('data', {})
    except:
        return {}

def get_working_dates():
    """Kalau weekend, mundur ke hari Jumat"""
    today = date.today()
    if today.weekday() == 5:  # Sabtu
        today = today - timedelta(days=1)
    elif today.weekday() == 6:  # Minggu
        today = today - timedelta(days=2)
    yesterday = today - timedelta(days=1)
    return today.isoformat(), yesterday.isoformat()

def fetch_kota_malang():
    print("Fetching Kota Malang...")
    old_data = load_old('kota_malang')
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
                harga_lama = old_data.get(nama_str, {}).get('harga', harga_num)
                hasil[nama_str] = {
                    "harga": harga_num,
                    "harga_lama": harga_lama,
                    "harga_raw": harga_str,
                    "tanggal": date.today().isoformat()
                }
        if hasil:
            print(f"Kota Malang: {len(hasil)} komoditas")
            return hasil
        else:
            print("Kota Malang: scrape kosong, pakai data lama")
            return old_data
    except Exception as e:
        print(f"Error Kota Malang: {e}, pakai data lama")
        return old_data

def fetch_sp2kp(kode_kab_kota, kode_provinsi, nama_wilayah, filename):
    print(f"Fetching SP2KP {nama_wilayah}...")
    try:
        today_iso, yesterday_iso = get_working_dates()
        print(f"  Pakai tanggal: {today_iso} vs {yesterday_iso}")

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

        # Kalau masih kosong, fallback ke data lama
        if not items:
            print(f"  Data kosong, pakai data lama")
            old = load_old(filename)
            if old:
                print(f"  Fallback: {len(old)} komoditas dari file lama")
                return old
            return {}

        hasil = {}
        for item in items:
            nama = item.get('variant_nama', '')
            harga = item.get('harga', 0) or item.get('harga_pembanding', 0)
            harga_lama = item.get('harga_pembanding', 0) or harga
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
        return load_old(filename)

def fetch_pihps_nasional():
    print("Fetching SP2KP Nasional...")
    return fetch_sp2kp("", "35", "Nasional", "pihps_nasional")

# Buat folder data
os.makedirs('data', exist_ok=True)

# Fetch semua
kota_malang = fetch_kota_malang()
kota_batu = fetch_sp2kp("3579", "35", "Kota Batu", "kota_batu")
pihps = fetch_pihps_nasional()

# Simpan ke JSON (hanya kalau ada data)
if kota_malang:
    with open('data/kota_malang.json', 'w') as f:
        json.dump({"updated": date.today().isoformat(), "data": kota_malang}, f, ensure_ascii=False, indent=2)

if kota_batu:
    with open('data/kota_batu.json', 'w') as f:
        json.dump({"updated": date.today().isoformat(), "data": kota_batu}, f, ensure_ascii=False, indent=2)

if pihps:
    with open('data/pihps_nasional.json', 'w') as f:
        json.dump({"updated": date.today().isoformat(), "data": pihps}, f, ensure_ascii=False, indent=2)

print("Selesai!")
