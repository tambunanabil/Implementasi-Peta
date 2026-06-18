import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import numpy as np
import sqlite3

# --- 1. PENGATURAN HALAMAN DASAR ---
st.set_page_config(page_title="Sistem Informasi Lahan Kentang", layout="wide", initial_sidebar_state="collapsed")

# Pengaturan Memori Sesi (Navigasi)
if 'page' not in st.session_state:
    st.session_state.page = 'beranda'
if 'clicked_lat' not in st.session_state:
    st.session_state.clicked_lat = None
    st.session_state.clicked_lon = None

# --- 2. CUSTOM CSS: BACKGROUND BAGUS, PANEL RAPI, TANPA IKON AI ---
st.markdown("""
    <style>
    /* Menyembunyikan sidebar bawaan */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    header { visibility: hidden !important; }

    /* Latar Belakang Pertanian yang Sebelumnya Anda Sukai */
    .stApp {
        background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.6)), url("https://images.unsplash.com/photo-1516253593875-bd7ba052fbc5?q=80&w=1600&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }

    /* Membungkus seluruh konten dengan panel putih transparan yang rapi (Aman dari error) */
    .block-container {
        background-color: rgba(255, 255, 255, 0.95) !important;
        padding: 3rem 4rem !important;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        max-width: 1100px !important;
        margin-top: 3rem !important;
        margin-bottom: 3rem !important;
    }

    /* Desain Tombol Elegan Formal */
    .stButton>button {
        background-color: #1e4620;
        color: white;
        border-radius: 6px;
        padding: 12px 15px;
        font-weight: 600;
        letter-spacing: 0.5px;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #2d6a4f;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI DATA ANTI-GAGAL ---
@st.cache_data(ttl=600)
def load_data():
    try:
        conn = sqlite3.connect('database_lahan.db')
        df = pd.read_sql_query("SELECT * FROM titik_acuan", conn)
        conn.close()
    except:
        try:
            df = pd.read_excel('Data_Kesesuaian.xlsx')
            if 'Lat' in df.columns and 'Lon' in df.columns:
                df['Lat'] = df['Lat'].ffill()
                df['Lon'] = df['Lon'].ffill()
        except:
            return pd.DataFrame()
            
    if not df.empty and 'Lat' in df.columns and 'Lon' in df.columns:
        df = df.dropna(subset=['Lat', 'Lon'])
    return df

def get_elevation(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        res = requests.get(url).json()
        return res["elevation"][0] if "elevation" in res else None
    except: return None

def hitung_jarak_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

df_data = load_data()

# ==========================================
# HALAMAN 1: BERANDA (FORMAL & COMPACT)
# ==========================================
if st.session_state.page == 'beranda':
    st.markdown("<h1 style='text-align: center; color: #1e4620; font-family: sans-serif; font-weight: 800;'>Sistem Informasi Spasial Lahan Kentang</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px; color: #555;'>Platform Evaluasi Agroklimat dan Distribusi Hara Pulau Jawa</p>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 20px; margin-bottom: 30px;'>", unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Masuk ke Peta Kesesuaian Lahan", use_container_width=True):
            st.session_state.page = 'fitur_peta'
            st.rerun()
    with col_btn2:
        if st.button("Masuk ke Rekomendasi Pemupukan", use_container_width=True):
            st.session_state.page = 'fitur_pupuk'
            st.rerun()

# ==========================================
# HALAMAN 2: PETA KESESUAIAN
# ==========================================
elif st.session_state.page == 'fitur_peta':
    
    col_judul, col_kembali = st.columns([4, 1])
    with col_judul:
        st.markdown("<h3 style='color: #1e4620; margin:0;'>Model Prediksi Kesesuaian Lahan</h3>", unsafe_allow_html=True)
    with col_kembali:
        if st.button("Kembali ke Beranda", use_container_width=True):
            st.session_state.page = 'beranda'
            st.rerun()
            
    st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

    col_input, col_peta = st.columns([1.2, 2.8])
    
    with col_input:
        st.markdown("<h5 style='color: #333;'>Parameter Analisis</h5>", unsafe_allow_html=True)
        radius_km = st.slider("Radius Batas Toleransi (Km)", 1.0, 15.0, 3.0, 0.5)
        ph_manual = st.number_input("Input Data pH Lokal (Opsional)", 0.0, 14.0, 0.0, 0.1)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if not df_data.empty:
            st.success(f"Status Sistem: {len(df_data)} titik data terhubung")
        else:
            st.error("Status Sistem: Data tidak ditemukan")
            
    with col_peta:
        # Peta Google Satellite Asli
        m = folium.Map(
            location=[-7.2106, 109.8941], 
            zoom_start=9, 
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
            attr='Google Maps'
        )
        
        # Plot Titik Referensi dengan Garis Tepi Putih agar Kontras
        if not df_data.empty:
            for _, row in df_data.iterrows():
                kategori = str(row.get('Kecocokan', '')).strip().lower()
                
                if kategori == 'cocok': warna = '#00FF00'
                elif kategori == 'netral': warna = '#FFFF00'
                else: warna = '#FF0000'

                ph_tanah = row.get('PH_S1', 'N/A')
                elev = row.get('Elevasi', 'N/A')
                
                popup_text = f"""
                <div style='font-family: sans-serif; font-size: 12px;'>
                    <b>Kategori:</b> {kategori.upper()}<br>
                    <b>Elevasi:</b> {elev} mdpl<br>
                    <b>pH (S1):</b> {ph_tanah}
                </div>
                """
                
                folium.CircleMarker(
                    location=[row['Lat'], row['Lon']],
                    radius=6, 
                    color='white', 
                    weight=1.5, 
                    fill=True, 
                    fill_color=warna, 
                    fill_opacity=1.0,
                    popup=folium.Popup(popup_text, max_width=200)
                ).add_to(m)

        # Plot Penanda Klik Pengguna
        if st.session_state.clicked_lat is not None:
            folium.Marker(
                location=[st.session_state.clicked_lat, st.session_state.clicked_lon],
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
            
        map_interaction = st_folium(m, use_container_width=True, height=450, returned_objects=["last_clicked"])

    if map_interaction and map_interaction.get("last_clicked"):
        lat_klik = map_interaction["last_clicked"]["lat"]
        lon_klik = map_interaction["last_clicked"]["lng"]
        
        if st.session_state.clicked_lat != lat_klik or st.session_state.clicked_lon != lon_klik:
            st.session_state.clicked_lat = lat_klik
            st.session_state.clicked_lon = lon_klik
            st.rerun()

    # --- HASIL PREDIKSI FORMAL ---
    if st.session_state.clicked_lat is not None:
        st.markdown("<hr style='margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.markdown("<h5 style='color: #333;'>Hasil Evaluasi Spasial</h5>", unsafe_allow_html=True)
        
        lat_eval = st.session_state.clicked_lat
        lon_eval = st.session_state.clicked_lon
        
        st.write(f"**Koordinat Uji:** {lat_eval:.5f}, {lon_eval:.5f}")
        
        with st.spinner("Mengekstraksi data satelit dan memproses jarak spasial..."):
            elevasi_satelit = get_elevation(lat_eval, lon_eval)
            
            if not df_data.empty and elevasi_satelit is not None:
                st.write(f"**Elevasi Permukaan:** {elevasi_satelit:.1f} mdpl")
                
                df_working = df_data.copy()
                df_working['Jarak_Km'] = df_working.apply(lambda r: hitung_jarak_haversine(lat_eval, lon_eval, r['Lat'], r['Lon']), axis=1)
                df_terfilter = df_working[df_working['Jarak_Km'] <= radius_km]
                
                if df_terfilter.empty:
                    st.error(f"EVALUASI: Di Luar Jangkauan. Tidak ditemukan data historis dalam radius {radius_km} km.")
                else:
                    elev_min, elev_max = df_terfilter['Elevasi'].min(), df_terfilter['Elevasi'].max()
                    
                    if elevasi_satelit < (elev_min - 50.0) or elevasi_satelit > (elev_max + 50.0):
                        st.error(f"EVALUASI: Tidak Cocok. Ketinggian melampaui batas toleransi wilayah terdekat ({elev_min:.0f} - {elev_max:.0f} mdpl).")
                    else:
                        hitung_suara = df_terfilter['Kecocokan'].str.lower().value_counts()
                        
                        if len(hitung_suara) > 1 and hitung_suara.iloc[0] == hitung_suara.iloc[1]:
                            st.warning("EVALUASI: Netral. Karakteristik data referensi di sekitar titik uji memiliki rasio seimbang.")
                        else:
                            suara_dominan = hitung_suara.idxmax()
                            if suara_dominan == 'cocok':
                                st.success("EVALUASI: Cocok. Mayoritas observasi di sekitar lokasi ini merekomendasikan kelayakan budidaya.")
                            elif suara_dominan == 'netral':
                                st.warning("EVALUASI: Netral. Zonasi di sekitar lokasi uji didominasi karakteristik lahan marginal.")
                            else:
                                st.error("EVALUASI: Tidak Cocok. Mayoritas observasi historis tidak merekomendasikan komoditas ini.")
            else:
                st.error("Sistem gagal menarik parameter elevasi dari server satelit.")

# ==========================================
# HALAMAN 3: REKOMENDASI PEMUPUKAN
# ==========================================
elif st.session_state.page == 'fitur_pupuk':
    col_judul, col_kembali = st.columns([4, 1])
    with col_judul:
        st.markdown("<h3 style='color: #1e4620; margin:0;'>Dasbor Rekomendasi Pemupukan</h3>", unsafe_allow_html=True)
    with col_kembali:
        if st.button("Kembali ke Beranda", use_container_width=True):
            st.session_state.page = 'beranda'
            st.rerun()
            
    st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.info("Modul kalkulasi matematis untuk dosis nutrisi tanah sedang dalam tahap integrasi.")