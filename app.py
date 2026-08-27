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
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
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
        # CEK & PERBAIKI PRIVATE KEY (REVISI TOTAL)
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


        # Ubah \n teks menjadi newline asli jika ada
        if "\\n" in private_key:
            private_key = private_key.replace(
                "\\n",
                "\n"
            )

        # Bersihkan spasi berlebih, pecah per baris, dan gabungkan kembali secara rapi
        lines = [
            line.strip()
            for line in private_key.splitlines()
            if line.strip()
        ]
        
        private_key = "\n".join(lines) + "\n"


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
            "-----END PRIVATE KEY-----\n"
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
            .get_all_values()
        )


        if len(all_pelanggan) > 1:

            for row in reversed(
                all_pelanggan
            ):

                if (
                    row
                    and row[0]
                    and "." in row[0]
                ):

                    last_opj = row[0]

                    parts = last_opj.split(".")


                    if (
                        parts[0].isdigit()
                    ):

                        next_number = (
                            int(parts[0]) + 1
                        )

                        break


    except Exception:

        pass


# ============================================================
# HEADER
# ============================================================

st.title(
    "🚀 Aplikasi Order Penjualan (OPJ)"
)

st.write(
    "Terhubung langsung dengan Google Sheets "
    "**Input OPJ**."
)


# ============================================================
# SESSION STATE
# ============================================================

if (
    "selected_products"
    not in st.session_state
):

    st.session_state.selected_products = []


# ============================================================
# FORM UTAMA
# ============================================================

st.subheader(
    "📝 Form Input / Edit OPJ"
)


# ============================================================
# PENCARIAN OPJ LAMA
# ============================================================

with st.container():

    st.markdown(
        "🔍 **Cari OPJ Lama (Untuk Edit/Update)**"
    )


    col_search1, col_search2 = (
        st.columns([3, 1])
    )


    with col_search1:

        search_opj_input = st.text_input(
            "Cari No OPJ",
            placeholder="Contoh: 181.RP.2026",
            label_visibility="collapsed"
        )


    with col_search2:

        btn_search = st.button(
            "Cari",
            use_container_width=True
        )


    # ========================================================
    # PROSES PENCARIAN
    # ========================================================

    if (
        btn_search
        and search_opj_input
    ):

        if ss:

            try:

                # ------------------------------------------------
                # CARI DATA PELANGGAN
                # ------------------------------------------------

                sh_pelanggan = (
                    ss.worksheet(
                        "Data Pelanggan"
                    )
                )


                data_p = (
                    sh_pelanggan
                    .get_all_values()
                )


                found_p = False


                for row in data_p:

                    if (
                        row
                        and row[0].strip().lower()
                        == search_opj_input
                        .strip()
                        .lower()
                    ):

                        st.session_state[
                            "edit_no_opj"
                        ] = row[0]


                        st.session_state[
                            "edit_tanggal"
                        ] = (
                            row[1]
                            if len(row) > 1
                            else ""
                        )


                        st.session_state[
                            "edit_pic"
                        ] = (
                            row[2]
                            if len(row) > 2
                            else "-- Pilih --"
                        )


                        st.session_state[
                            "edit_nama"
                        ] = (
                            row[3]
                            if len(row) > 3
                            else ""
                        )


                        st.session_state[
                            "edit_perusahaan"
                        ] = (
                            row[4]
                            if len(row) > 4
                            else ""
                        )


                        st.session_state[
                            "edit_alamat"
                        ] = (
                            row[5]
                            if len(row) > 5
                            else ""
                        )


                        st.session_state[
                            "edit_telp"
                        ] = (
                            row[6]
                            if len(row) > 6
                            else ""
                        )


                        st.session_state[
                            "edit_email"
                        ] = (
                            row[7]
                            if len(row) > 7
                            else ""
                        )


                        found_p = True

                        break


                # ------------------------------------------------
                # CARI DETAIL PRODUK
                # ------------------------------------------------

                sh_detail = (
                    ss.worksheet(
                        "Detail OPJ"
                    )
                )


                data_d = (
                    sh_detail
                    .get_all_values()
                )


                loaded_items = []


                for row in data_d:

                    if (
                        len(row) > 7
                        and row[1]
                        .strip()
                        .lower()
                        == search_opj_input
                        .strip()
                        .lower()
                    ):

                        raw_h = (
                            row[7]
                            .replace(",", "")
                            .replace(".", "")
                            if row[7]
                            else "0"
                        )


                        try:

                            harga = float(
                                raw_h
                            )

                        except ValueError:

                            harga = 0.0


                        try:

                            qty = int(
                                row[6]
                            )

                        except (
                            ValueError,
                            TypeError
                        ):

                            qty = 1


                        loaded_items.append({

                            "idProduk": row[2],

                            "namaProduk": row[3],

                            "spesifikasi": row[4],

                            "stn": (
                                row[5]
                                if row[5]
                                else "Unit"
                            ),

                            "qty": qty,

                            "harga": harga,

                        })


                # ------------------------------------------------
                # HASIL PENCARIAN
                # ------------------------------------------------

                if found_p:

                    st.session_state[
                        "selected_products"
                    ] = loaded_items


                    st.success(
                        f"Data OPJ {search_opj_input} "
                        "berhasil dimuat! "
                        "Silakan cek di bawah."
                    )


                    st.rerun()


                else:

                    st.warning(
                        f"Nomor OPJ "
                        f"'{search_opj_input}' "
                        "tidak ditemukan."
                    )


            except Exception as e:

                st.error(
                    f"❌ Gagal mencari data: {e}"
                )


st.markdown("---")


# ============================================================
# DEFAULT VALUE
# ============================================================

def_pic = st.session_state.get(
    "edit_pic",
    "-- Pilih --"
)

def_nama = st.session_state.get(
    "edit_nama",
    ""
)

def_perusahaan = st.session_state.get(
    "edit_perusahaan",
    ""
)

def_alamat = st.session_state.get(
    "edit_alamat",
    ""
)

def_telp = st.session_state.get(
    "edit_telp",
    ""
)

def_email = st.session_state.get(
    "edit_email",
    ""
)


# ============================================================
# DATA OPJ
# ============================================================

col1, col2, col3 = (
    st.columns([1, 2, 2])
)


# ============================================================
# PIC
# ============================================================

with col1:

    pic_options = [
        "-- Pilih --",
        "RP",
        "SG"
    ]


    pic_code = st.selectbox(
        "PIC Code",
        pic_options,
        index=(
            pic_options.index(
                def_pic
            )
            if def_pic in pic_options
            else 0
        )
    )


# ============================================================
# NOMOR OPJ
# ============================================================

with col2:

    current_year = str(
        datetime.date.today().year
    )


    if (
        "edit_no_opj"
        in st.session_state
        and st.session_state[
            "edit_no_opj"
        ]
    ):

        no_opj_auto = (
            st.session_state[
                "edit_no_opj"
            ]
        )

    else:

        no_opj_auto = (

            f"{next_number}."
            f"{pic_code}."
            f"{current_year}"

            if pic_code != "-- Pilih --"

            else

            f"{next_number}.---."
            f"{current_year}"
        )


    st.text_input(
        "No OPJ (Otomatis)",
        value=no_opj_auto,
        disabled=True
    )


# ============================================================
# TANGGAL
# ============================================================

with col3:

    tanggal_default = (
        datetime.date.today()
    )


    edit_tanggal = (
        st.session_state.get(
            "edit_tanggal",
            ""
        )
    )


    if edit_tanggal:

        try:

            tanggal_default = (
                datetime.datetime
                .strptime(
                    edit_tanggal,
                    "%Y-%m-%d"
                )
                .date()
            )

        except ValueError:

            tanggal_default = (
                datetime.date.today()
            )


    tanggal_opj = st.date_input(
        "Tanggal",
        tanggal_default
    )


# ============================================================
# PELANGGAN
# ============================================================

col_pel1, col_pel2 = (
    st.columns(2)
)


with col_pel1:

    nama_pelanggan = st.text_input(
        "Nama Pelanggan",
        value=def_nama,
        placeholder="Nama Pemesan"
    )


with col_pel2:

    perusahaan = st.text_input(
        "Perusahaan",
        value=def_perusahaan,
        placeholder="PT / CV / Instansi"
    )


alamat = st.text_area(
    "Alamat Lengkap",
    value=def_alamat,
    placeholder="Alamat pengiriman..."
)


# ============================================================
# KONTAK
# ============================================================

col_kontak1, col_kontak2 = (
    st.columns(2)
)


with col_kontak1:

    no_telp = st.text_input(
        "No Telp",
        value=def_telp,
        placeholder="08xxxxxxxxxx"
    )


with col_kontak2:

    email = st.text_input(
        "Email",
        value=def_email,
        placeholder="email@domain.com"
    )


# ============================================================
# PRODUK
# ============================================================

st.markdown("---")

st.subheader(
    "🛒 Detail Produk Order"
)


product_placeholder = (
    "Ketik atau pilih nama produk untuk mencari..."
)


selected_product_name = st.selectbox(
    "Cari & Tambah Produk",
    [product_placeholder]
    + [
        p["nama"]
        for p in product_list
    ]
)


# ============================================================
# TAMBAH PRODUK
# ============================================================

if st.button(
    "➕ Tambah Produk ke List"
):

    if (
        selected_product_name
        != product_placeholder
    ):

        prod_obj = next(
            (
                p
                for p in product_list
                if p["nama"]
                == selected_product_name
            ),
            None
        )


        if prod_obj:

            st.session_state[
                "selected_products"
            ].append({

                "idProduk":
                    prod_obj["id"],

                "namaProduk":
                    prod_obj["nama"],

                "spesifikasi":
                    prod_obj["spesifikasi"],

                "stn":
                    "Unit",

                "qty":
                    1,

                "harga":
                    prod_obj["harga"],

            })


            st.rerun()


# ============================================================
# TAMPILKAN PRODUK
# ============================================================

if st.session_state[
    "selected_products"
]:

    st.markdown("---")


    for idx, item in enumerate(
        st.session_state[
            "selected_products"
        ]
    ):

        with st.container():

            st.markdown(
                f"**{item['namaProduk']}**"
            )


            st.caption(
                item["spesifikasi"]
                if item["spesifikasi"]
                else
                "Tidak ada spesifikasi khusus"
            )


            cols = st.columns(
                [1.5, 1, 2, 1]
            )


            with cols[0]:

                st.session_state[
                    "selected_products"
                ][idx]["stn"] = (
                    st.text_input(
                        "Stn",
                        item["stn"],
                        key=f"stn_{idx}"
                    )
                )


            with cols[1]:

                st.session_state[
                    "selected_products"
                ][idx]["qty"] = (
                    st.number_input(
                        "Qty",
                        min_value=1,
                        value=int(
                            item["qty"]
                        ),
                        key=f"qty_{idx}"
                    )
                )


            with cols[2]:

                st.session_state[
                    "selected_products"
                ][idx]["harga"] = (
                    st.number_input(
                        "Harga",
                        min_value=0.0,
                        value=float(
                            item["harga"]
                        ),
                        step=1000.0,
                        key=f"harga_{idx}"
                    )
                )


            with cols[3]:

                st.write("")


                if st.button(
                    "❌",
                    key=f"del_{idx}",
                    help="Hapus produk"
                ):

                    st.session_state[
                        "selected_products"
                    ].pop(idx)


                    st.rerun()


            st.markdown("---")


# ============================================================
# SIMPAN / UPDATE OPJ
# ============================================================

if st.button(
    "💾 SIMPAN / UPDATE OPJ",
    type="primary",
    use_container_width=True
):

    if pic_code == "-- Pilih --":

        st.error(
            "❌ PIC Code belum dipilih!"
        )

    elif not st.session_state[
        "selected_products"
    ]:

        st.error(
            "❌ Pilih minimal 1 produk!"
        )

    elif not ss:

        st.error(
            "❌ Koneksi Google Sheets "
            "belum terhubung!"
        )

    else:

        try:

            sheet_pelanggan = (
                ss.worksheet(
                    "Data Pelanggan"
                )
            )

            sheet_detail = (
                ss.worksheet(
                    "Detail OPJ"
                )
            )

            all_p = (
                sheet_pelanggan
                .get_all_values()
            )

            row_index_to_update = None

            for idx_row, row in enumerate(
                all_p
            ):

                if (
                    row
                    and row[0]
                    .strip()
                    .lower()
                    == no_opj_auto
                    .strip()
                    .lower()
                ):

                    row_index_to_update = (
                        idx_row + 1
                    )

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
                    [new_pelanggan_row]
                )

            else:

                sheet_pelanggan.append_row(
                    new_pelanggan_row
                )

            all_d = (
                sheet_detail
                .get_all_values()
            )

            rows_to_delete = []

            for idx_d, row_d in enumerate(
                all_d
            ):

                if (
                    len(row_d) > 1
                    and row_d[1]
                    .strip()
                    .lower()
                    == no_opj_auto
                    .strip()
                    .lower()
                ):

                    rows_to_delete.append(
                        idx_d + 1
                    )

            for r_idx in sorted(
                rows_to_delete,
                reverse=True
            ):

                sheet_detail.delete_rows(
                    r_idx
                )

            for item in (
                st.session_state[
                    "selected_products"
                ]
            ):

                jumlah = (
                    float(item["qty"])
                    * float(item["harga"])
                )

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

                sheet_detail.append_row(
                    detail_row
                )

            if (
                "edit_no_opj"
                in st.session_state
            ):

                del st.session_state[
                    "edit_no_opj"
                ]

            if (
                "edit_tanggal"
                in st.session_state
            ):

                del st.session_state[
                    "edit_tanggal"
                ]

            if (
                "edit_pic"
                in st.session_state
            ):

                del st.session_state[
                    "edit_pic"
                ]

            if (
                "edit_nama"
                in st.session_state
            ):

                del st.session_state[
                    "edit_nama"
                ]

            if (
                "edit_perusahaan"
                in st.session_state
            ):

                del st.session_state[
                    "edit_perusahaan"
                ]

            if (
                "edit_alamat"
                in st.session_state
            ):

                del st.session_state[
                    "edit_alamat"
                ]

            if (
                "edit_telp"
                in st.session_state
            ):

                del st.session_state[
                    "edit_telp"
                ]

            if (
                "edit_email"
                in st.session_state
            ):

                del st.session_state[
                    "edit_email"
                ]

            st.session_state[
                "selected_products"
            ] = []

            st.success(
                f"🎉 Data OPJ {no_opj_auto} "
                "berhasil disimpan/diperbarui "
                "ke Google Sheets!"
            )

        except Exception as e:

            st.error(
                "❌ Terjadi kesalahan saat "
                f"menyimpan data:\n\n{e}"
            )
