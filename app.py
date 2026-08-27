import base64
from datetime import datetime
import os
import json
import streamlit as st
from google.oauth2 import service_account
import gspread

# --- Konfigurasi Halaman Streamlit (Harus di paling atas setelah import) ---
st.set_page_config(
    page_title="Aplikasi Order Penjualan (OPJ) - CVSK",
    page_icon="🚀",
    layout="wide",
)

# --- KONEKSI GOOGLE SHEETS MENGGUNAKAN FILE JSON LOKAL ---
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SERVICE_ACCOUNT_FILE = "service_account.json"

@st.cache_resource
def init_connection():
  try:
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=scope
    )
    return gspread.authorize(creds)
  except Exception as e:
    return None

gc = init_connection()

if gc is None:
  st.error("Gagal terhubung ke Google Sheets. Periksa kembali file service_account.json.")
  st.stop()

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

st.markdown("---")

# --- FORM INPUT ORDER PENJUALAN (OPJ) ---
st.subheader("📝 Form Input Order Penjualan")

with st.form("form_opj"):
    col1, col2 = st.columns(2)
    
    with col1:
        no_opj = st.text_input("Nomor OPJ", placeholder="Contoh: OPJ/CVSK/2026/001")
        nama_customer = st.text_input("Nama Customer / Klien", placeholder="Masukkan nama customer")
        tanggal_order = st.date_input("Tanggal Order", datetime.now())
        
    with col2:
        proyek = st.text_input("Nama Proyek / Unit", placeholder="Contoh: Mesin Presto / Biodigester / Parfum")
        catatan = st.text_area("Catatan Tambahan", placeholder="Instruksi khusus pengiriman atau spesifikasi...")

    # Tombol Submit Form
    submit_button = st.form_submit_button(label="💾 Simpan & Kirim ke Google Sheets")

    if submit_button:
        if not no_opj or not nama_customer:
            st.warning("⚠️ Nomor OPJ dan Nama Customer wajib diisi!")
        else:
            try:
                # Buka spreadsheet (Sesuaikan nama file Google Sheets kamu di sini)
                # Contoh: spreadsheet = gc.open("Database_OPJ_CVSK")
                # sheet = spreadsheet.worksheet("Sheet1")
                # sheet.append_row([str(tanggal_order), no_opj, nama_customer, proyek, catatan])
                
                st.success(f"✅ Data OPJ **{no_opj}** berhasil diproses!")
            except Exception as e:
                st.error(f"Gagal menyimpan data ke Google Sheets: {e}")
