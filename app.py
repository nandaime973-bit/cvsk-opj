import base64
from datetime import datetime
import os
import json
import streamlit as st
from google.oauth2 import service_account
import gspread

# --- KONEKSI GOOGLE SHEETS MENGGUNAKAN FILE JSON LOKAL ---
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SERVICE_ACCOUNT_FILE = "service_account.json"

try:
  # Membaca file JSON service account langsung dari folder repository
  creds = service_account.Credentials.from_service_account_file(
      SERVICE_ACCOUNT_FILE, scopes=scope
  )
  gc = gspread.authorize(creds)
  # Koneksi berhasil, variabel 'gc' siap digunakan untuk memanggil Google Sheets
except Exception as e:
  st.error(f"Gagal terhubung ke Google Sheets: {e}")

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Aplikasi Order Penjualan (OPJ) - CVSK",
    page_icon="🚀",
    layout="wide",
)


# --- FUNGSI HELPER LOGO BASE64 ---
def get_image_base64(filepath):
  if os.path.exists(filepath):
    with open(filepath, "rb") as f:
      data = f.read()
    return base64.b64encode(data).decode("utf-8")
  return ""


# Memuat logo dari folder lokal
logo_base64 = get_image_base64("CVSK Logo baru.png")
logo_src = (
    f"data:image/png;base64,{logo_base64}"
    if logo_base64
    else ""
)

# --- HEADER APLIKASI ---
st.markdown(
    "🚀 ## Aplikasi Order Penjualan (OPJ) - PT Cipta Visi Sinar Kencana"
)
st.write(
    "Terhubung langsung dengan Google Sheets Input OPJ (Dilengkapi Logo"
    " Perusahaan & Template Resmi A4 Portrait)."
)

# --- LANJUTKAN KODE UTAMA KAMU DI BAWAH INI ---
# (Pastikan fungsi pemanggilan sheet menggunakan variabel 'gc' di atas)
