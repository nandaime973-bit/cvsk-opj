import datetime
import streamlit as st
import gspread
from google.oauth2 import service_account

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Aplikasi Order Penjualan (OPJ)", page_icon="🚀", layout="centered"
)

# --- KONEKSI LANGSUNG MENGGUNAKAN DICTIONARY INTERNAL (ANTI GAGAL) ---
@st.cache_resource
def get_google_sheets_connection():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        # Masukkan kredensial langsung dalam bentuk dictionary Python
        creds_dict = {
            "type": "service_account",
            "project_id": "opj-bot",
            "private_key_id": "GANTI_DENGAN_PRIVATE_KEY_ID_ANDA_JIKA_PERLU",
            "private_key": '''-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...
(PASTE SELURUH KODE PRIVATE KEY ANDA DISINI, JANGAN ADA YANG HILANG)
...
-----END PRIVATE KEY-----''',
            "client_email": "opj-connector@opj-bot.iam.gserviceaccount.com",
            "client_id": "GANTI_DENGAN_CLIENT_ID_ANDA",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/opj-connector%40opj-bot.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }

        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=scope
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open("Input OPJ")
        return spreadsheet
    except Exception as e:
        st.error(f"Gagal terhubung ke Google Sheets: {e}")
        return None

ss = get_google_sheets_connection()

# Ambil data produk awal & hitung nomor OPJ otomatis
product_list = []
next_number = 182  # Disesuaikan dari data terakhir di sheet (181)

if ss:
    try:
        sheet_db = ss.worksheet("Database Produk")
        db_data = sheet_db.get_all_values()
        for i in range(1, len(db_data)):
            if len(db_data[i]) > 1 and db_data[i][1]:
                raw_harga = (
                    str(db_data[i][3])
                    .replace(",", "")
                    .replace(".", "")
                    .strip()
                )
                harga_val = float(raw_harga) if raw_harga else 0.0
                product_list.append({
                    "id": db_data[i][0],
                    "nama": db_data[i][1],
                    "spesifikasi": db_data[i][2] if len(db_data[i]) > 2 else "",
                    "harga": harga_val,
                })
    except Exception as e:
        st.warning(f"Catatan: Belum bisa membaca sheet 'Database Produk' - {e}")

    try:
        sheet_pelanggan = ss.worksheet("Data Pelanggan")
        all_pelanggan = sheet_pelanggan.get_all_values()
        if len(all_pelanggan) > 1:
            for row in reversed(all_pelanggan):
                if row and row[0] and "." in row[0]:
                    last_opj = row[0]
                    parts = last_opj.split(".")
                    if parts[0].isdigit():
                        next_number = int(parts[0]) + 1
                        break
    except Exception as e:
        pass

# --- HEADER APLIKASI ---
st.title("🚀 Aplikasi Order Penjualan (OPJ)")
st.write("Terhubung langsung dengan Google Sheets **Input OPJ**.")

if "selected_products" not in st.session_state:
    st.session_state.selected_products = []

# --- FORM UTAMA INPUT OPJ ---
st.subheader("📝 Form Input / Edit OPJ")

# --- FITUR PENCARIAN OPJ LAMA (UNTUK EDIT/UPDATE) ---
with st.container():
    st.markdown("🔍 **Cari OPJ Lama (Untuk Edit/Update)**")
    col_search1, col_search2 = st.columns([3, 1])
    with col_search1:
        search_opj_input = st.text_input(
            "Cari No OPJ",
            placeholder="Contoh: 181.RP.2026",
            label_visibility="collapsed",
        )
    with col_search2:
        btn_search = st.button("Cari", use_container_width=True)

    if btn_search and search_opj_input:
        if ss:
            try:
                sh_pelanggan = ss.worksheet("Data Pelanggan")
                data_p = sh_pelanggan.get_all_values()
                found_p = False
                for row in data_p:
                    if row and row[0].strip().lower() == search_opj_input.strip().lower():
                        st.session_state["edit_no_opj"] = row[0]
                        st.session_state["edit_tanggal"] = row[1]
                        st.session_state["edit_pic"] = row[2]
                        st.session_state["edit_nama"] = row[3]
                        st.session_state["edit_perusahaan"] = row[4]
                        st.session_state["edit_alamat"] = row[5]
                        st.session_state["edit_telp"] = row[6]
                        st.session_state["edit_email"] = row[7] if len(row) > 7 else ""
                        found_p = True
                        break

                sh_detail = ss.worksheet("Detail OPJ")
                data_d = sh_detail.get_all_values()
                loaded_items = []
                for row in data_d:
                    if (
                        len(row) > 7
                        and row[1].strip().lower() == search_opj_input.strip().lower()
                    ):
                        raw_h = row[7].replace(",", "").replace(".", "") if row[7] else "0"
                        loaded_items.append({
                            "idProduk": row[2],
                            "namaProduk": row[3],
                            "spesifikasi": row[4],
                            "stn": row[5] if row[5] else "Unit",
                            "qty": int(row[6]) if row[6].isdigit() else 1,
                            "harga": float(raw_h) if raw_h else 0.0,
                        })

                if found_p:
                    st.session_state.selected_products = loaded_items
                    st.success(
                        f"Data OPJ {search_opj_input} berhasil dimuat! Silakan cek di bawah."
                    )
                    st.rerun()
                else:
                    st.warning(f"Nomor OPJ '{search_opj_input}' tidak ditemukan.")
            except Exception as e:
                st.error(f"Gagal mencari data: {e}")

st.markdown("---")

def_pic = st.session_state.get("edit_pic", "-- Pilih --")
def_nama = st.session_state.get("edit_nama", "")
def_perusahaan = st.session_state.get("edit_perusahaan", "")
def_alamat = st.session_state.get("edit_alamat", "")
def_telp = st.session_state.get("edit_telp", "")
def_email = st.session_state.get("edit_email", "")

col1, col2, col3 = st.columns([1, 2, 2])
with col1:
    pic_code = st.selectbox(
        "PIC Code",
        ["-- Pilih --", "RP", "SG"],
        index=(
            ["-- Pilih --", "RP", "SG"].index(def_pic)
            if def_pic in ["-- Pilih --", "RP", "SG"]
            else 0
        ),
    )
with col2:
    current_year = str(datetime.date.today().year)
    if "edit_no_opj" in st.session_state and st.session_state["edit_no_opj"]:
        no_opj_auto = st.session_state["edit_no_opj"]
    else:
        no_opj_auto = (
            f"{next_number}.{pic_code}.{current_year}"
            if pic_code != "-- Pilih --"
            else f"{next_number}.---.{current_year}"
        )
    st.text_input("No OPJ (Otomatis)", value=no_opj_auto, disabled=True)
with col3:
    tanggal_opj = st.date_input("Tanggal", datetime.date.today())

col_pel1, col_pel2 = st.columns(2)
with col_pel1:
    nama_pelanggan = st.text_input(
        "Nama Pelanggan", value=def_nama, placeholder="Nama Pemesan"
    )
with col_pel2:
    perusahaan = st.text_input(
        "Perusahaan", value=def_perusahaan, placeholder="PT / CV / Instansi"
    )

alamat = st.text_area(
    "Alamat Lengkap", value=def_alamat, placeholder="Alamat pengiriman..."
)

col_kontak1, col_kontak2 = st.columns(2)
with col_kontak1:
    no_telp = st.text_input("No Telp", value=def_telp, placeholder="08xxxxxxxxxx")
with col_kontak2:
    email = st.text_input("Email", value=def_email, placeholder="email@domain.com")

st.markdown("---")
st.subheader("🛒 Detail Produk Order")

selected_product_name = st.selectbox(
    "Cari & Tambah Produk",
    ["Ketik atau pilih nama produk untuk mencari..."]
    + [p["nama"] for p in product_list],
)

if st.button("➕ Tambah Produk ke List"):
    if selected_product_name != "Ketik atau pilih nama produk untuk mencari...":
        prod_obj = next(
            (p for p in product_list if p["nama"] == selected_product_name), None
        )
        if prod_obj:
            st.session_state.selected_products.append({
                "idProduk": prod_obj["id"],
                "namaProduk": prod_obj["nama"],
                "spesifikasi": prod_obj["spesifikasi"],
                "stn": "Unit",
                "qty": 1,
                "harga": prod_obj["harga"],
            })
            st.rerun()

if st.session_state.selected_products:
    st.markdown("---")
    for idx, item in enumerate(st.session_state.selected_products):
        with st.container():
            st.markdown(f"**{item['namaProduk']}**")
            st.caption(
                item["spesifikasi"]
                if item["spesifikasi"]
                else "Tidak ada spesifikasi khusus"
            )

            cols = st.columns([1.5, 1, 2, 1])
            with cols[0]:
                st.session_state.selected_products[idx]["stn"] = st.text_input(
                    "Stn", item["stn"], key=f"stn_{idx}"
                )
            with cols[1]:
                st.session_state.selected_products[idx]["qty"] = st.number_input(
                    "Qty", min_value=1, value=int(item["qty"]), key=f"qty_{idx}"
                )
            with cols[2]:
                st.session_state.selected_products[idx]["harga"] = st.number_input(
                    "Harga",
                    value=float(item["harga"]),
                    key=f"harga_{idx}",
                    step=1000.0,
                )
            with cols[3]:
                st.write("")
                if st.button("❌", key=f"del_{idx}", help="Hapus produk"):
                    st.session_state.selected_products.pop(idx)
                    st.rerun()
            st.markdown("---")

if st.button(
    "💾 SIMPAN / UPDATE OPJ", type="primary", use_container_width=True
):
    if pic_code == "-- Pilih --":
        st.error("PIC Code belum dipilih!")
    elif not st.session_state.selected_products:
        st.error("Pilih minimal 1 produk!")
    elif not ss:
        st.error("Koneksi Google Sheets belum terhubung!")
    else:
        try:
            sheet_pelanggan = ss.worksheet("Data Pelanggan")
            sheet_detail = ss.worksheet("Detail OPJ")

            all_p = sheet_pelanggan.get_all_values()
            row_index_to_update = None
            for idx_row, row in enumerate(all_p):
                if row and row[0].strip().lower() == no_opj_auto.strip().lower():
                    row_index_to_update = idx_row + 1
                    break

            new_pelanggan_row = [
                no_opj_auto,
                str(tanggal_opj),
                pic_code,
                nama_pelanggan,
                perusahaan,
                alamat,
                no_telp,
                email,
            ]

            if row_index_to_update:
                sheet_pelanggan.update(
                    f"A{row_index_to_update}:H{row_index_to_update}",
                    [new_pelanggan_row],
                )
            else:
                sheet_pelanggan.append_row(new_pelanggan_row)

            all_d = sheet_detail.get_all_values()
            rows_to_delete = []
            for idx_d, row_d in enumerate(all_d):
                if (
                    len(row_d) > 1
                    and row_d[1].strip().lower() == no_opj_auto.strip().lower()
                ):
                    rows_to_delete.append(idx_d + 1)

            for r_idx in sorted(rows_to_delete, reverse=True):
                sheet_detail.delete_rows(r_idx)

            for item in st.session_state.selected_products:
                jumlah = float(item["qty"]) * float(item["harga"])
                detail_row = [
                    str(tanggal_opj),
                    no_opj_auto,
                    item["idProduk"],
                    item["namaProduk"],
                    item["spesifikasi"],
                    item["stn"],
                    item["qty"],
                    item["harga"],
                    jumlah,
                ]
                sheet_detail.append_row(detail_row)

            if "edit_no_opj" in st.session_state:
                del st.session_state["edit_no_opj"]
            st.session_state.selected_products = []

            st.success(
                f"Data OPJ {no_opj_auto} berhasil disimpan/diperbarui ke Google Sheets! 🎉"
            )
        except Exception as e:
            st.error(f"Terjadi kesalahan saat menyimpan data: {e}")
