import base64
import datetime
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

# Konfigurasi Halaman Streamlit
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


# --- KONEKSI KE GOOGLE SHEETS ---
@st.cache_resource
def get_google_sheets_connection():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", scope
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
next_number = 165

if ss:
  try:
    sheet_db = ss.worksheet("Database Produk")
    db_data = sheet_db.get_all_values()
    for i in range(1, len(db_data)):
      if db_data[i][1]:
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
            "spesifikasi": db_data[i][2],
            "harga": harga_val,
        })
  except Exception as e:
    st.warning(f"Catatan: Belum bisa membaca sheet 'Database Produk' - {e}")

  try:
    sheet_pelanggan = ss.worksheet("Data Pelanggan")
    all_pelanggan = sheet_pelanggan.get_all_values()
    if len(all_pelanggan) > 1:
      last_row = all_pelanggan[-1]
      last_opj = last_row[0]
      parts = last_opj.split(".")
      if parts[0].isdigit():
        next_number = int(parts[0]) + 1
  except Exception as e:
    pass

# --- HEADER APLIKASI ---
st.title("🚀 Aplikasi Order Penjualan (OPJ) - PT Cipta Visi Sinar Kencana")
st.write(
    "Terhubung langsung dengan Google Sheets **Input OPJ** (Dilengkapi Logo"
    " Perusahaan & Template Resmi A4 Portrait)."
)

if "selected_products" not in st.session_state:
  st.session_state.selected_products = []

# --- FITUR PENCARIAN OPJ LAMA (UNTUK EDIT & TEMPLATE) ---
with st.container():
  st.markdown("🔍 **Cari OPJ Lama (Untuk Edit & Lihat Template)**")
  col_search1, col_search2 = st.columns([4, 1])
  with col_search1:
    search_opj_input = st.text_input(
        "Cari No OPJ",
        placeholder="Contoh: 018.OPJ/CS.2023 atau 165.SG.2026",
        label_visibility="collapsed",
    )
  with col_search2:
    btn_search = st.button("Cari Data", use_container_width=True)

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
            st.session_state["edit_biaya_kirim"] = (
                float(row[8].replace(",", "").replace(".", ""))
                if len(row) > 8 and row[8]
                else 0.0
            )
            st.session_state["edit_biaya_instalasi"] = (
                float(row[9].replace(",", "").replace(".", ""))
                if len(row) > 9 and row[9]
                else 0.0
            )
            st.session_state["edit_delivery_time"] = (
                row[10]
                if len(row) > 10
                else "Pengiriman dan serah terima produk pada H+ 25 hari kerja"
            )
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
            loaded_items.append({
                "idProduk": row[2],
                "namaProduk": row[3],
                "spesifikasi": row[4],
                "stn": row[5] if row[5] else "Unit",
                "qty": int(row[6]) if row[6].isdigit() else 1,
                "harga": float(row[7].replace(",", "").replace(".", ""))
                if row[7]
                else 0.0,
            })

        if found_p:
          st.session_state.selected_products = loaded_items
          st.success(
              f"Data OPJ {search_opj_input} berhasil dimuat ke Form & Template!"
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
def_b_kirim = st.session_state.get("edit_biaya_kirim", 0.0)
def_b_instalasi = st.session_state.get("edit_biaya_instalasi", 0.0)
def_del_time = st.session_state.get(
    "edit_delivery_time",
    "Pengiriman dan serah terima produk pada H+ 25 hari kerja sejak PO dan"
    " syarat pembayaran dipenuhi",
)

# Layout Form Input
col_f1, col_f2 = st.columns(2)

with col_f1:
  st.subheader("📝 Input / Edit Data Pelanggan")
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
    st.text_input("No OPJ", value=no_opj_auto, disabled=True)
  with col3:
    tanggal_opj = st.date_input("Tanggal", datetime.date.today())

  nama_pelanggan = st.text_input("Kepada Yth (Nama)", value=def_nama)
  perusahaan = st.text_input("Perusahaan", value=def_perusahaan)
  alamat = st.text_area("Alamat", value=def_alamat)

  col_k1, col_k2 = st.columns(2)
  with col_k1:
    no_telp = st.text_input("Telp", value=def_telp)
  with col_k2:
    email = st.text_input("Email", value=def_email)

with col_f2:
  st.subheader("💰 Biaya & Pengiriman")
  biaya_kirim = st.number_input(
      "Biaya Kirim / Mobilisasi (IDR)",
      min_value=0.0,
      value=float(def_b_kirim),
      step=1000.0,
  )
  biaya_instalasi = st.number_input(
      "Biaya Pasang / Instalasi (IDR)",
      min_value=0.0,
      value=float(def_b_instalasi),
      step=1000.0,
  )
  delivery_time = st.text_input(
      "Ketentuan Waktu / Delivery Time", value=def_del_time
  )
  lokasi_kirim = st.text_input(
      "Keterangan Tempat Kirim", value="Gudang Pembeli"
  )

st.markdown("---")
st.subheader("🛒 Detail Produk Order")

selected_product_name = st.selectbox(
    "Cari & Tambah Produk dari Database",
    ["Ketik atau pilih nama produk..."] + [p["nama"] for p in product_list],
)

if st.button("➕ Tambah Produk"):
  if selected_product_name != "Ketik atau pilih nama produk...":
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
  for idx, item in enumerate(st.session_state.selected_products):
    with st.container():
      cols = st.columns([3, 1, 1, 2, 1])
      with cols[0]:
        st.markdown(f"**{item['namaProduk']}**")
        st.caption(item["spesifikasi"])
      with cols[1]:
        st.session_state.selected_products[idx]["stn"] = st.text_input(
            "Stn", item["stn"], key=f"stn_{idx}"
        )
      with cols[2]:
        st.session_state.selected_products[idx]["qty"] = st.number_input(
            "Qty", min_value=1, value=int(item["qty"]), key=f"qty_{idx}"
        )
      with cols[3]:
        st.session_state.selected_products[idx]["harga"] = st.number_input(
            "Harga",
            value=float(item["harga"]),
            key=f"harga_{idx}",
            step=1000.0,
        )
      with cols[4]:
        st.write("")
        if st.button("❌ Hapus", key=f"del_{idx}"):
          st.session_state.selected_products.pop(idx)
          st.rerun()

st.markdown("---")

# Tombol Simpan / Update
if st.button(
    "💾 SIMPAN / UPDATE OPJ KE GOOGLE SHEETS",
    type="primary",
    use_container_width=True,
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
          biaya_kirim,
          biaya_instalasi,
          delivery_time,
          lokasi_kirim,
      ]

      if row_index_to_update:
        sheet_pelanggan.update(
            f"A{row_index_to_update}:L{row_index_to_update}",
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

      st.success(
          f"Data OPJ {no_opj_auto} berhasil disimpan / diperbarui ke Google"
          " Sheets!"
      )
    except Exception as e:
      st.error(f"Terjadi kesalahan saat menyimpan data: {e}")


# =====================================================================
# --- PREVIEW TEMPLATE CETAK (FORMAT KERTAS A4 PORTRAIT) ---
# =====================================================================
st.markdown("---")
st.header("📄 Preview Lembar Kerja Template OPJ (Format A4 Portrait)")
st.info(
    "Tampilan di bawah ini disesuaikan dengan proporsi fisik kertas A4"
    " Portrait standar dokumen resmi PT Cipta Visi Sinar Kencana."
)

sub_total = sum(
    item["qty"] * item["harga"] for item in st.session_state.selected_products
)
ppn = sub_total * 0.11
grand_total = sub_total + biaya_kirim + biaya_instalasi + ppn


def fmt(val):
  return f"{val:,.0f}".replace(",", ".")


def terbilang(n):
  if n == 0:
    return "Nol Rupiah"
  angka = [
      "",
      "Satu",
      "Dua",
      "Tiga",
      "Empat",
      "Lima",
      "Enam",
      "Tujuh",
      "Delapan",
      "Sembilan",
      "Sepuluh",
      "Sebelas",
  ]
  def to_words(x):
    if x < 12:
      return angka[x]
    elif x < 20:
      return to_words(x - 10) + " Belas"
    elif x < 100:
      return (
          to_words(x // 10)
          + " Puluh "
          + (to_words(x % 10) if x % 10 != 0 else "")
      )
    elif x < 200:
      return "Seratus " + to_words(x - 100)
    elif x < 1000:
      return (
          to_words(x // 100)
          + " Ratus "
          + (to_words(x % 100) if x % 100 != 0 else "")
      )
    elif x < 2000:
      return "Seribu " + to_words(x - 1000)
    elif x < 1000000:
      return (
          to_words(x // 1000)
          + " Ribu "
          + (to_words(x % 1000) if x % 1000 != 0 else "")
      )
    elif x < 1000000000:
      return (
          to_words(x // 1000000)
          + " Juta "
          + (to_words(x % 1000000) if x % 1000000 != 0 else "")
      )
    elif x < 1000000000000:
      return (
          to_words(x // 1000000000)
          + " Miliar "
          + (to_words(x % 1000000000) if x % 1000000000 != 0 else "")
      )
    return ""

  hasil = to_words(int(n)).strip()
  return hasil.title() + " Rupiah"


terbilang_str = terbilang(grand_total)

rows_html = ""
if st.session_state.selected_products:
  for i, item in enumerate(st.session_state.selected_products, 1):
    tot_item = item["qty"] * item["harga"]
    rows_html += f"""
        <tr>
            <td style="border: 1px solid black; text-align: center; padding: 4px;">{i}</td>
            <td style="border: 1px solid black; padding: 4px;"><b>{item["namaProduk"]}</b></td>
            <td style="border: 1px solid black; padding: 4px; font-size: 9.5px; color: #333;">{item["spesifikasi"]}</td>
            <td style="border: 1px solid black; text-align: center; padding: 4px;">{item["stn"]}</td>
            <td style="border: 1px solid black; text-align: center; padding: 4px;">{item["qty"]}</td>
            <td style="border: 1px solid black; text-align: right; padding: 4px;">{fmt(item["harga"])}</td>
            <td style="border: 1px solid black; text-align: right; padding: 4px;">{fmt(tot_item)}</td>
        </tr>
        """
else:
  rows_html = """
    <tr>
        <td colspan="7" style="border: 1px solid black; text-align: center; padding: 15px; color: #777;">Belum ada produk yang dipilih. Silakan tambah produk di atas.</td>
    </tr>
    """

# Template HTML dengan struktur bawah yang presisi sama persis dengan master aslinya
template_html = f"""
<div style="
    width: 794px; 
    min-height: 1123px; 
    margin: 0 auto; 
    background: white; 
    color: black; 
    border: 1px solid #d3d3d3; 
    box-shadow: 0 0 10px rgba(0,0,0,0.15); 
    padding: 35px; 
    box-sizing: border-box; 
    font-family: 'Arial', sans-serif; 
    font-size: 10px; 
    line-height: 1.25;">
    
    <!-- HEADER UTAMA DENGAN KOP LOGO -->
    <table width="100%" style="border-collapse: collapse; border: 1px solid black; font-size: 9.5px;">
        <tr>
            <td style="border: 1px solid black; padding: 5px; width: 38%; vertical-align: middle;">
                <table width="100%" style="border-collapse: collapse;">
                    <tr>
                        <td style="width: 22%; vertical-align: middle; text-align: center; padding-right: 4px;">
                            <img src="{logo_src}" alt="Logo CVSK" style="max-width: 42px; height: auto;">
                        </td>
                        <td style="width: 78%; vertical-align: middle;">
                            <b style="font-size: 9.5px;">PT. CIPTA VISI SINAR KENCANA</b><br>
                            <span style="font-size: 8px;">Jl Raya Banjaran No 390 Pameungpeuk KM 13<br>Bandung Selatan 40376</span>
                        </td>
                    </tr>
                </table>
                <div style="font-size: 8px; margin-top: 3px; border-top: 1px solid #ccc; padding-top: 2px;">
                    No Telp : +62-22-87800115-87800083<br>
                    E-Mail : marketing@kencanaonline.com
                </div>
            </td>
            <td style="border: 1px solid black; padding: 5px; text-align: center; width: 32%; vertical-align: middle;">
                <b style="font-size: 11.5px; letter-spacing: 0.5px;">ORDER PENJUALAN (OPJ)</b><br>
                <span style="font-size: 9px; color: #555;">Quotation</span>
            </td>
            <td style="border: 1px solid black; padding: 5px; width: 30%; vertical-align: top; font-size: 9px;">
                <table width="100%" style="border-collapse: collapse;">
                    <tr>
                        <td width="42%" style="padding: 0.5px 0;"><b>Kode Formulir</b></td>
                        <td width="5%">:</td>
                        <td width="53%">02-FORM/CVSK/MS/4.4</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5px 0;"><b>PIC Code</b></td>
                        <td>:</td>
                        <td>{pic_code}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5px 0;"><b>Nomor OPJ</b></td>
                        <td>:</td>
                        <td>{no_opj_auto}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5px 0;"><b>Tanggal OPJ</b></td>
                        <td>:</td>
                        <td>{str(tanggal_opj)}</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    
    <br>
    
    <!-- BILL TO / KEPADA YTH -->
    <table width="100%" style="font-size: 10px; border-collapse: collapse;">
        <tr>
            <td width="15%" style="padding: 0.5px 0;"><b>Bill To</b></td>
            <td width="2%"></td>
            <td width="83%"></td>
        </tr>
        <tr>
            <td style="padding: 0.5px 0;"><b>Kepada Yth</b></td>
            <td>:</td>
            <td><b>{nama_pelanggan}</b></td>
        </tr>
        <tr>
            <td style="padding: 0.5px 0;"><b>Perusahaan</b></td>
            <td>:</td>
            <td><b>{perusahaan}</b></td>
        </tr>
        <tr>
            <td style="padding: 0.5px 0;"><b>Alamat</b></td>
            <td>:</td>
            <td>{alamat}</td>
        </tr>
        <tr>
            <td style="padding: 0.5px 0;"><b>Telp</b></td>
            <td>:</td>
            <td>{no_telp}</td>
        </tr>
        <tr>
            <td style="padding: 0.5px 0;"><b>Email</b></td>
            <td>:</td>
            <td>{email}</td>
        </tr>
    </table>
    
    <br>
    
    <!-- TABEL ITEM PRODUK -->
    <table width="100%" style="border-collapse: collapse; border: 1px solid black; font-size: 9.5px;">
        <tr style="background-color: #f2f2f2; text-align: center; font-weight: bold;">
            <th style="border: 1px solid black; padding: 4px; width: 4%;">No</th>
            <th style="border: 1px solid black; padding: 4px; width: 21%;">Nama Produk</th>
            <th style="border: 1px solid black; padding: 4px; width: 38%;">Spesifikasi / Keterangan</th>
            <th style="border: 1px solid black; padding: 4px; width: 7%;">Stn</th>
            <th style="border: 1px solid black; padding: 4px; width: 6%;">Qty</th>
            <th style="border: 1px solid black; padding: 4px; width: 12%;">Harga Stn</th>
            <th style="border: 1px solid black; padding: 4px; width: 12%;">Jumlah</th>
        </tr>
        {rows_html}
        
        <!-- BAGIAN TOTAL, TERBILANG & SYARAT PENYERAHAN -->
        <tr>
            <td colspan="5" rowspan="5" style="border: 1px solid black; padding: 6px; vertical-align: top; font-size: 9.5px;">
                <b>Terbilang:</b><br>
                <i style="color: #000080;">"{terbilang_str}"</i><br><br>
                <b>Syarat Penyerahan:</b><br>
                - Tempat: {lokasi_kirim}<br>
                - Waktu: {delivery_time}
            </td>
            <td style="border: 1px solid black; padding: 4px; text-align: right;"><b>Total [IDR]</b></td>
            <td style="border: 1px solid black; padding: 4px; text-align: right;"><b>{fmt(sub_total)}</b></td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 4px; text-align: right;">Biaya Kirim</td>
            <td style="border: 1px solid black; padding: 4px; text-align: right;">{fmt(biaya_kirim)}</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 4px; text-align: right;">Biaya Instalasi</td>
            <td style="border: 1px solid black; padding: 4px; text-align: right;">{fmt(biaya_instalasi)}</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 4px; text-align: right;">PPN 11%</td>
            <td style="border: 1px solid black; padding: 4px; text-align: right;">{fmt(ppn)}</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 4px; text-align: right; background-color: #ffffcc;"><b>Grand Total [IDR]</b></td>
            <td style="border: 1px solid black; padding: 4px; text-align: right; background-color: #ffffcc;"><b>{fmt(grand_total)}</b></td>
        </tr>
    </table>
    
    <br>
    
    <!-- KETENTUAN & REKENING -->
    <table width="100%" style="font-size: 9px; border: 1px solid black; border-collapse: collapse; padding: 5px;">
        <tr>
            <td>
                <b>Transfer to Account Bank:</b> Mandiri KC Asia Afrika Bandung | <b>A/N: PT. Cipta Visi Sinar Kencana</b> | <b>No Rek: 1300011461731</b><br>
                <b>Dengan ketentuan:</b><br>
                o OPJ ini berlaku selama 20 (duapuluh) hari sejak diterbitkan.<br>
                o Harga total diatas sudah termasuk pengiriman dan pemasangan (sesuai rincian).<br>
                o Harga diatas sudah termasuk PPN 11%.
            </td>
        </tr>
    </table>
    
    <br><br>
    
    <!-- TANDA TANGAN -->
    <table width="100%" style="font-size: 9.5px; text-align: center;">
        <tr>
            <td width="50%">
                <b>PT. Cipta Visi Sinar Kencana</b><br><br><br><br><br>
                <b><u>Ir. Sonson Garsoni</u></b><br>
                Marketing
            </td>
            <td width="50%">
                <b>Pembeli</b><br><br><br><br><br>
                <b><u>( ........................................ )</u></b><br>
                Authorized Signature
            </td>
        </tr>
    </table>

</div>
"""

# Tombol Cetak / Print Browser
col_p1, col_p2, col_p3 = st.columns([2, 2, 2])
with col_p2:
  st.markdown(
      """
        <script>
        function printDiv() {
            window.print();
        }
        </script>
        <button onclick="window.print()" style="width: 100%; background-color: #ff4b4b; color: white; padding: 10px 20px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer;">
            🖨️ CETAK / SIMPAN KE PDF (A4)
        </button>
        """,
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)
st.html(template_html)