import streamlit as st
import pandas as pd
import re
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Automation Engineering", layout="wide")

# --- FUNGSI DETEKSI PIN (Replikasi RegEx VBA) ---
def detect_pin_count(combined_desc):
    combined_desc = str(combined_desc).upper()
    qty_pins = 0
    
    # Pola multi-pin (2x10, 5X20)
    re_multi = re.search(r'(\d{1,2})\s*[xX]\s*(\d{1,3})', combined_desc)
    # Pola single-pin (40PIN, QFP64, SOIC-16)
    re_single = re.search(r'(\d{1,5})[\-\s]?(PIN|PINS|QFN|QFP|BGA|SOIC|MSOP|TSOP|TSSOP|TQFP|POS|POSN)|(PIN|PINS|QFN|QFP|BGA|SOIC|MSOP|TSOP|TSSOP|TQFP|POS|POSN)[\-\s]?(\d{1,5})', combined_desc)
    # Pola konektor (CON015F)
    re_conn = re.search(r'\bCON[\-\s]?0*([0-9]{1,4})([MFP]?)\b', combined_desc)

    if re_single:
        qty_pins = int(re_single.group(1)) if re_single.group(1) else int(re_single.group(4))
    elif re_conn:
        qty_pins = int(re_conn.group(1))
    elif re_multi:
        qty_pins = int(re_multi.group(1)) * int(re_multi.group(2))
        
    return qty_pins

# --- NAVIGASI SIDEBAR ---
st.sidebar.title("🚀 Menu Utama")
halaman = st.sidebar.radio("Pilih Modul:", ["Segregation BOM", "AI Researcher", "RFQ Tracking"])

# ---------------------------------------------------------
# MODUL 1: SEGREGATION BOM (LOGIKA 3 TAHAP VBA)
# ---------------------------------------------------------
if halaman == "Segregation BOM":
    st.header("📦 BOM Segregation Engine")
    
    # Sidebar untuk Rules (Pengganti Access DB)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Database Rules")
    rules_file = st.sidebar.file_uploader("Upload Rules (Excel)", type=['xlsx'])

    upload_file = st.file_uploader("Upload File BOM Customer (Excel)", type=["xlsx"])
    
    if upload_file and rules_file:
        df_bom = pd.read_excel(upload_file)
        df_rules = pd.read_excel(rules_file)
        
        st.subheader("Mapping Kolom")
        cols = df_bom.columns.tolist()
        c1, c2, c3, c4 = st.columns(4)
        desc_col = c1.selectbox("Kolom Description", cols)
        mpn_col = c2.selectbox("Kolom MPN", cols)
        qty_col = c3.selectbox("Kolom Qty", cols)
        loc_col = c4.selectbox("Kolom Location/Designator", cols)
        
        if st.button("Jalankan Segregasi 3 Tahap"):
            # 1. Pre-processing (Eliminasi baris kosong/qty 0)
            df_bom = df_bom.dropna(subset=[loc_col])
            df_bom = df_bom[df_bom[qty_col] > 0].copy()
            
            # 2. Siapkan Kolom Segregasi (Header Kuning di VBA)
            seg_headers = ["CHIP", "SOT", "SOIC", "PTS SOIC", "QFP", "PTS QFP", "MI/BE", "PTS MI/BE"]
            for h in seg_headers:
                df_bom[h] = 0

            # 3. Looping Klasifikasi (Logika Tahap 1, 2, 3)
            for index, row in df_bom.iterrows():
                desc = str(row[desc_col]).upper()
                mpn = str(row[mpn_col]).upper()
                combined = f"{mpn} {desc}"
                qty = row[qty_col]
                
                found_cat = ""
                pts = 0

                # --- TAHAP 1: PRIORITAS SMT (SOT, SOIC, QFP) ---
                for _, r in df_rules.iterrows():
                    cat = str(r['Category']).upper()
                    if any(x in cat for x in ["SOT", "SOIC", "QFP"]):
                        k1 = str(r['Keyword1']).upper()
                        k2 = str(r['Keyword2']).upper()
                        if k1 in combined and (k2 == 'NAN' or k2 == '' or k2 in combined):
                            found_cat = cat
                            pts = r['PTS'] if pd.notna(r['PTS']) else detect_pin_count(combined)
                            break
                
                # --- TAHAP 2: CHIP & THT (MI/BE) ---
                if not found_cat:
                    for _, r in df_rules.iterrows():
                        cat = str(r['Category']).upper()
                        if any(x in cat for x in ["CHIP", "MI/BE", "THT"]):
                            k1 = str(r['Keyword1']).upper()
                            k2 = str(r['Keyword2']).upper()
                            if k1 in combined and (k2 == 'NAN' or k2 == '' or k2 in combined):
                                found_cat = cat
                                pts = r['PTS'] if pd.notna(r['PTS']) else detect_pin_count(combined)
                                break

                # --- TAHAP 3: NONCOMP ---
                if not found_cat:
                    # Logika NONCOMP bisa ditambahkan di sini sesuai kebutuhan
                    pass

                # 4. Penulisan Hasil (WriteCategoryResult di VBA)
                if "CHIP" in found_cat: df_bom.at[index, "CHIP"] = qty
                elif "SOT" in found_cat: df_bom.at[index, "SOT"] = qty
                elif "SOIC" in found_cat:
                    df_bom.at[index, "SOIC"] = qty
                    df_bom.at[index, "PTS SOIC"] = qty * pts
                elif "QFP" in found_cat:
                    df_bom.at[index, "QFP"] = qty
                    df_bom.at[index, "PTS QFP"] = qty * pts
                elif any(x in found_cat for x in ["MI/BE", "THT"]):
                    df_bom.at[index, "MI/BE"] = qty
                    df_bom.at[index, "PTS MI/BE"] = qty * pts

            st.success("Klasifikasi Selesai!")
            st.dataframe(df_bom)
            
            # Download Hasil sebagai Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_bom.to_excel(writer, index=False)
            
            st.download_button("📥 Download Hasil Segregasi", output.getvalue(), "Hasil_Segregasi.xlsx")
    else:
        st.info("Harap upload file BOM dan file Rules (Excel) di sidebar untuk memulai.")

# ---------------------------------------------------------
# MODUL 2: AI RESEARCHER (TETAP)
# ---------------------------------------------------------
elif halaman == "AI Researcher":
    st.header("🤖 AI Researcher (Perplexity)")
    mpn = st.text_input("Masukkan MPN:")
    if st.button("Tanya AI"):
        st.info(f"Fitur ini akan segera terhubung ke API Perplexity untuk mencari data {mpn}.")

# ---------------------------------------------------------
# MODUL 3: RFQ TRACKING (TETAP)
# ---------------------------------------------------------
elif halaman == "RFQ Tracking":
    st.header("📊 Tracking RFQ")
    st.write("Fitur tracking Excel Anda akan diletakkan di sini.")
