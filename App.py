import streamlit as st
import pandas as pd
import re

# Seting halaman agar lebar
st.set_page_config(page_title="Automation Engineering", layout="wide")

# --- NAVIGASI SIDEBAR ---
st.sidebar.title("Menu Utama")
halaman = st.sidebar.radio("Pilih Modul:", ["Segregation BOM", "AI Researcher", "RFQ Tracking"])

# --- MODUL 1: SEGREGATION BOM ---
if halaman == "Segregation BOM":
    st.header("📦 BOM Segregation")
    upload_file = st.file_uploader("Upload File BOM (Excel)", type=["xlsx"])
    
    if upload_file:
        df = pd.read_excel(upload_file)
        kolom_desc = st.selectbox("Pilih Kolom Deskripsi:", df.columns)
        
        if st.button("Proses Sekarang"):
            # Contoh Logika Deteksi PIN sederhana
            def hitung_pin(text):
                match = re.search(r'(\d+)\s*(PIN|QFP|SOIC)', str(text).upper())
                return match.group(1) if match else "0"
            
            df['Detected_PIN'] = df[kolom_desc].apply(hitung_pin)
            st.success("Proses Berhasil!")
            st.dataframe(df)
            
            # Download Hasil
            st.download_button("Download Hasil", df.to_csv(index=False).encode('utf-8'), "Hasil_Segregasi.csv")

# --- MODUL 2: AI RESEARCHER ---
elif halaman == "AI Researcher":
    st.header("🤖 AI Researcher (Perplexity)")
    mpn = st.text_input("Masukkan MPN:")
    if st.button("Tanya AI"):
        st.info(f"Fitur ini akan segera terhubung ke API Perplexity untuk mencari data {mpn}.")

# --- MODUL 3: RFQ TRACKING ---
elif halaman == "RFQ Tracking":
    st.header("📊 Tracking RFQ")
    st.write("Fitur tracking Excel Anda akan diletakkan di sini.")
