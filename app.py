import datetime
import streamlit as st
import gspread
from google.oauth2 import service_account


# ============================================================
# KONFIGURASI HALAMAN
# ============================================================

st.set_page_config(
    page_title="Aplikasi Order Penjualan (OPJ)",
    page_icon="🚀",
    layout="centered"
)


# ============================================================
# KONEKSI GOOGLE SHEETS
# ============================================================

@st.cache_resource
def get_google_sheets_connection():

    scope = [
        "[https://www.googleapis.com/auth/spreadsheets](https://www.googleapis.com/auth/spreadsheets)",
        "[https://www.googleapis.com/auth/drive](https://www.googleapis.com/auth/drive)",
    ]

    try:

        # ----------------------------------------------------
        # CEK STREAMLIT SECRETS
        # ----------------------------------------------------

        if "gcp_service_account" not in st.secrets:

            st.error(
                "❌ Credential Google belum ditemukan.\n\n"
                "Jika menggunakan Streamlit Cloud, "
                "masukkan credential ke:\n"
                "Settings → Secrets"
            )

            return None


        # ----------------------------------------------------
        # AMBIL CREDENTIAL
        # ----------------------------------------------------

        creds_dict = dict(
            st.secrets["gcp_service_account"]
        )


        # ----------------------------------------------------
        # CEK PRIVATE KEY
        # ----------------------------------------------------

        if "private_key" not in creds_dict:

            st.error(
                "❌ private_key tidak ditemukan "
                "di Google Secrets."
            )

            return None


        private_key = str(
            creds_dict["private_key"]
        )


        # ----------------------------------------------------
        # PERBAIKI NEWLINE PRIVATE KEY
        # ----------------------------------------------------

        private_key = private_key.replace(
            "\\n",
            "\n"
        ).strip()


        # ----------------------------------------------------
        # VALIDASI FORMAT PEM
        # ----------------------------------------------------

        if not private_key.startswith(
            "-----BEGIN PRIVATE KEY-----"
        ):

            st.error(
                "❌ Format private key tidak valid.\n\n"
                "Private key harus dimulai dengan:\n"
                "-----BEGIN PRIVATE KEY-----"
            )

            return None


        if not private_key.endswith(
            "-----END PRIVATE KEY-----"
        ):

            st.error(
                "❌ Format private key tidak valid.\n\n"
                "Private key harus diakhiri dengan:\n"
                "-----END PRIVATE KEY-----"
            )

            return None


        # Masukkan private key yang sudah diperbaiki
        creds_dict["private_key"] = private_key


        # ----------------------------------------------------
        # BUAT GOOGLE CREDENTIALS
        # ----------------------------------------------------

        creds = (
            service_account
            .Credentials
            .from_service_account_info(
                creds_dict,
                scopes=scope
            )
        )


        # ----------------------------------------------------
        # AUTHORIZE GOOGLE SHEETS
        # ----------------------------------------------------

        client = gspread.authorize(
            creds
        )


        # ----------------------------------------------------
        # BUKA SPREADSHEET
        # ----------------------------------------------------

        spreadsheet = client.open(
            "Input OPJ"
        )


        return spreadsheet


    except Exception as e:

        st.error(
            "❌ Gagal terhubung ke Google Sheets:\n\n"
            f"{e}"
        )

        return None


# ============================================================
# CONNECT KE GOOGLE SHEETS
# ============================================================

ss = get_google_sheets_connection()


# ============================================================
# DATA PRODUK
# ============================================================

product_list = []

# Nomor awal jika belum ada data
next_number = 182


if ss:

    # ========================================================
    # DATABASE PRODUK
    # ========================================================

    try:

        sheet_db = ss.worksheet(
            "Database Produk"
        )

        db_data = sheet_db.get_all_values()


        for i in range(
            1,
            len(db_data)
        ):

            if (
                len(db_data[i]) > 1
                and db_data[i][1]
            ):

                raw_harga = (
                    str(
                        db_data[i][3]
                    )
                    .replace(",", "")
                    .replace(".", "")
                    .strip()
                    if len(db_data[i]) > 3
                    else "0"
                )


                try:

                    harga_val = (
                        float(raw_harga)
                        if raw_harga
                        else 0.0
                    )

                except ValueError:

                    harga_val = 0.0


                product_list.append({

                    "id": db_data[i][0],

                    "nama": db_data[i][1],

                    "spesifikasi": (
                        db_data[i][2]
                        if len(db_data[i]) > 2
                        else ""
                    ),

                    "harga": harga_val,

                })


    except Exception as e:

        st.warning(
            "⚠️ Catatan: Belum bisa membaca "
            f"sheet 'Database Produk' - {e}"
        )


    # ========================================================
    # CARI NOMOR OPJ TERAKHIR
    # ========================================================

    try:

        sheet_pelanggan = ss.worksheet(
            "Data Pelanggan"
        )

        all_pelanggan = (
            sheet_pelanggan
            .get_all_
