import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import numpy as np

# --- 1. KONFIGURASI DAN NAVIGASI TOMBOL ---
st.set_page_config(page_title="Sistem Informasi Geografis Lahan Kentang", layout="wide", initial_sidebar_state="collapsed")

if 'page' not in st.session_state:
    st.session_state.page = 'beranda'
if 'clicked_lat' not in st.session_state:
    st.session_state.clicked_lat = None
    st.session_state.clicked_lon = None

# --- 2. CUSTOM CSS: ANTARMUKA WEB SOLID, RAPI, & ELEGAN ---
st.markdown("""
    <style>
    /* Hilangkan Komponen Bawaan */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { visibility: hidden !important; }
    
    /* Latar Belakang */
    .stApp {
        background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.5)), url("https://images.unsplash.com/photo-1516253593875-bd7ba052fbc5?q=80&w=1600&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }

    /* Wadah Konten Utama */
    .block-container {
        max-width: 1200px; /* Diperlebar sedikit agar peta lebih lega */
        margin: auto;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Panel Putih Utama */
    .main-panel {
        background-color: rgba(255, 255, 255, 0.98);
        padding: 30px 40px;
        border-radius: 10px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
    }

    /* Panel Kontrol Kiri (Agar Rapi dan Terpisah) */
    .control-panel {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e9ecef;
    }

    /* Tombol Navigasi */
    .stButton>button {
        background-color: #1e4620;
        color: white;
        border-radius: 6px;
        padding: 12px 20px;
        font-size: 15px;
        font-weight: 600;
        width: 100%;
        border: none;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #2d6a4f;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* Tombol Kembali */
    .btn-back>div>button {
        background-color: #6c757d !important;
        padding: 8px 15px !important;
        font-size: 14px !important;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE LOGIC SISTEM ---
@st.cache_data(ttl=600)
def query_database():
    try:
        conn = sqlite3.connect('database_lahan.db')
        df = pd.read_sql_query("SELECT * FROM titik_acuan", conn)
        conn.close()
        df = df.dropna(subset=['Lat', 'Lon']) 
        return df
    except Exception:
        return pd.DataFrame()

def get_elevation(lat, lon):
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
    try:
        res = requests.get(url).json()
        return res["elevation"][0] if "elevation" in res else None
    except: 
        return None

def hitung_jarak_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

df_data = query_database()

# ==========================================
# HALAMAN 1: BERANDA UTAMA 
# ==========================================
if st.session_state.page == 'beranda':
    st.markdown('<div class="main-panel">', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #1e4620; font-family: sans-serif; font-weight: 800;'>Sistem Informasi Spasial Lahan Kentang</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555; font-size: 16px;'>Silakan pilih modul analitik di bawah ini untuk memulai pemetaan wilayah produksi Pulau Jawa.</p>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Masuk ke Peta Kesesuaian Lahan"):
            st.session_state.page = 'fitur_peta'
            st.rerun()
    with col_btn2:
        if st.button("Masuk ke Rekomendasi Pemupukan"):
            st.session_state.page = 'fitur_pupuk'
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# HALAMAN 2: FITUR PETA KESESUAIAN LAHAN
# ==========================================
elif st.session_state.page == 'fitur_peta':
    st.markdown('<div class="main-panel">', unsafe_allow_html=True)
    
    # Header Navigasi Atas
    col_h, col_b = st.columns([4, 1])
    with col_h:
        st.markdown("<h3 style='color: #1e4620; margin:0; font-weight: 700;'>Model Prediksi Kesesuaian Lahan</h3>", unsafe_allow_html=True)
    with col_b:
        st.markdown('<div class="btn-back">', unsafe_allow_html=True)
        if st.button("Kembali ke Beranda"):
            st.session_state.page = 'beranda'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    
    # Layout Fitur: Proporsi disesuaikan agar peta lebih dominan dan rapi
    col_inputs, col_map_display = st.columns([1.2, 2.8])
    
    with col_inputs:
        # Kotak Panel Kontrol yang Rapi
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        st.markdown("<h5 style='color: #333; margin-bottom: 15px;'>⚙️ Parameter Analisis</h5>", unsafe_allow_html=True)
        
        radius_km = st.slider("Radius Batas (Km)", 1.0, 15.0, 3.0, 0.5)
        st.markdown("<br>", unsafe_allow_html=True)
        ph_manual = st.number_input("Input pH Lokal (Opsional)", 0.0, 14.0, 0.0, 0.1)
        
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        if not df_data.empty:
            st.success(f"🟢 **{len(df_data)}** Titik acuan aktif")
        else:
            st.error("🔴 Basis data terputus")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_map_display:
        # Peta Citra Satelit Google Maps
        m = folium.Map(
            location=[-7.2106, 109.8941], 
            zoom_start=9, 
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
            attr='Google Maps Satellite'
        )
        
        # Plot Sebaran Titik (Dengan Styling Border Putih agar TERLIHAT JELAS)
        if not df_data.empty:
            for _, row in df_data.iterrows():
                kategori_excel = str(row.get('Kecocokan', '')).strip().lower()
                
                # Warna fill (isi)
                if kategori_excel == 'cocok': 
                    warna_marker = '#00FF00' 
                elif kategori_excel == 'netral': 
                    warna_marker = '#FFFF00' 
                else: 
                    warna_marker = '#FF0000' 

                ph_tanah = row.get('PH_S1', 'N/A')
                
                popup_text = f"""
                <div style='font-family: sans-serif; font-size: 12px; min-width: 150px;'>
                    <b>Status Lahan:</b> <span style='color:{warna_marker}; background-color:#333; padding:2px 5px; border-radius:3px;'>{kategori_excel.upper()}</span><br>
                    <hr style='margin: 5px 0;'>
                    <b>Elevasi:</b> {row.get('Elevasi', 'N/A')} mdpl<br>
                    <b>pH (S1):</b> {ph_tanah}
                </div>
                """
                
                # SOLUSI KONTRAS: radius diperbesar (7), ditambah garis tepi putih (color='#ffffff'), opacity penuh (1.0)
                folium.CircleMarker(
                    location=[row['Lat'], row['Lon']],
                    radius=7, 
                    color='#ffffff',      # Garis tepi putih murni
                    weight=1.5,           # Ketebalan garis tepi
                    fill=True, 
                    fill_color=warna_marker, 
                    fill_opacity=1.0,     # Warna solid, tidak transparan
                    popup=folium.Popup(popup_text, max_width=250)
                ).add_to(m)

        # Plot Pin Interaktif (Marker Biru)
        if st.session_state.clicked_lat is not None:
            folium.Marker(
                location=[st.session_state.clicked_lat, st.session_state.clicked_lon],
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
            
        # Tampilkan Peta secara Responsif (Memenuhi kolom)
        map_interaction = st_folium(m, use_container_width=True, height=500, returned_objects=["last_clicked"])

    if map_interaction and map_interaction.get("last_clicked"):
        lat_klik = map_interaction["last_clicked"]["lat"]
        lon_klik = map_interaction["last_clicked"]["lng"]
        
        if st.session_state.clicked_lat != lat_klik or st.session_state.clicked_lon != lon_klik:
            st.session_state.clicked_lat = lat_klik
            st.session_state.clicked_lon = lon_klik
            st.rerun()

    # --- PANEL EVALUASI BAWAH ---
    if st.session_state.clicked_lat is not None:
        st.markdown("<hr style='margin-top: 30px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.markdown("#### 📊 Hasil Evaluasi Spasial Titik Pilihan")
        
        lat_eval = st.session_state.clicked_lat
        lon_eval = st.session_state.clicked_lon
        
        elevasi_satelit = get_elevation(lat_eval, lon_eval)
        
        if not df_data.empty and elevasi_satelit is not None:
            df_working = df_data.copy()
            df_working['Jarak_Km'] = df_working.apply(lambda r: hitung_jarak_haversine(lat_eval, lon_eval, r['Lat'], r['Lon']), axis=1)
            df_terfilter = df_working[df_working['Jarak_Km'] <= radius_km]
            
            # Membungkus hasil dalam container agar elegan
            with st.container():
                if df_terfilter.empty:
                    st.error(f"**DI LUAR JANGKAUAN:** Tidak ada titik acuan dalam radius {radius_km} km. Geser slider radius untuk memperluas pencarian.")
                else:
                    elev_min, elev_max = df_terfilter['Elevasi'].min(), df_terfilter['Elevasi'].max()
                    
                    if elevasi_satelit < (elev_min - 50.0) or elevasi_satelit > (elev_max + 50.0):
                        st.error(f"**TIDAK COCOK:** Ketinggian lokasi uji ({elevasi_satelit:.1f} mdpl) melampaui batas toleransi wajar wilayah terdekat ({elev_min:.0f} - {elev_max:.0f} mdpl).")
                    else:
                        hitung_suara = df_terfilter['Kecocokan'].str.lower().value_counts()
                        
                        if len(hitung_suara) > 1 and hitung_suara.iloc[0] == hitung_suara.iloc[1]:
                            st.warning(f"**NETRAL:** Parameter di sekitar titik uji memiliki kekuatan seimbang (50:50). Lahan mungkin marginal.")
                        else:
                            suara_dominan = hitung_suara.idxmax()
                            if suara_dominan == 'cocok':
                                st.success(f"**COCOK:** Lahan dengan ketinggian {elevasi_satelit:.1f} mdpl ini berada pada zonasi ideal budidaya berdasarkan mayoritas observasi historis.")
                            elif suara_dominan == 'netral':
                                st.warning(f"**NETRAL:** Zonasi di sekitar lokasi didominasi oleh karakteristik lahan marginal/netral.")
                            else:
                                st.error(f"**TIDAK COCOK:** Mayoritas observasi spasial terdekat tidak merekomendasikan komoditas ini.")
        else:
            st.info("Sistem sedang memuat data ketinggian satelit. Harap tunggu...")

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# HALAMAN 3: FITUR REKOMENDASI PEMUPUKAN
# ==========================================
elif st.session_state.page == 'fitur_pupuk':
    st.markdown('<div class="main-panel">', unsafe_allow_html=True)
    
    col_h2, col_b2 = st.columns([4, 1])
    with col_h2:
        st.markdown("<h3 style='color: #1e4620; margin:0;'>Dasbor Optimasi Rekomendasi Pemupukan</h3>", unsafe_allow_html=True)
    with col_b2:
        st.markdown('<div class="btn-back">', unsafe_allow_html=True)
        if st.button("Kembali ke Beranda"):
            st.session_state.page = 'beranda'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
            
    st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.info("Modul kalkulasi nutrisi tanah berbasis algoritma matematika sedang dipersiapkan untuk diintegrasikan.")
    st.markdown('</div>', unsafe_allow_html=True)