import json
import streamlit as st
import gspread
from google.oauth2 import service_account

@st.cache_resource
def get_google_sheets_connection():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        # Buka file JSON secara manual agar kita bisa perbaiki private_key-nya dulu
        with open("credentials.json", "r") as f:
            creds_dict = json.load(f)
            
        # Perbaiki format newline pada private_key di dalam JSON
        if "private_key" in creds_dict:
            priv_key = creds_dict["private_key"]
            if "\\n" in priv_key:
                priv_key = priv_key.replace("\\n", "\n")
            
            # Rapikan baris kuncinya
            lines = [line.strip() for line in priv_key.splitlines() if line.strip()]
            creds_dict["private_key"] = "\n".join(lines) + "\n"

        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=scope
        )
        
        client = gspread.authorize(creds)
        spreadsheet = client.open("Input OPJ")
        return spreadsheet
        
    except Exception as e:
        st.error(f"❌ Gagal terhubung ke Google Sheets:\n\n{e}")
        return None
