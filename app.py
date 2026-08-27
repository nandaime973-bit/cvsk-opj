import base64
from datetime import datetime
import os
import json
import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

# --- KONEKSI GOOGLE SHEETS MENGGUNAKAN STREAMLIT SECRETS ---
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

try:
  # Mengambil kredensial aman dari secrets.toml atau Streamlit Cloud Secrets
  creds_dict = dict(st.secrets["gcp_service_account"])
  creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
  gc = gspread.authorize(creds)
  # Koneksi berhasil, variabel 'gc' siap digunakan di bawah untuk memanggil sheet
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
