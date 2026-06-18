import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import numpy as np
import sqlite3

# --- 1. PENGATURAN HALAMAN DASAR ---
st.set_page_config(page_title="AgriGIS | Lahan Kentang", layout="wide", initial_sidebar_state="collapsed")

# --- 2. PENGATURAN STATE (MEMORI HALAMAN) ---
if 'page' not in st.session_state:
    st.session_state.page = 'beranda'
if 'clicked_lat' not in st.session_state:
    st.session_state.clicked_lat = None
    st.session_state.clicked_lon = None

# Menyembunyikan sidebar murni tanpa merusak warna latar
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    /* Mempercantik tombol agar elegan tapi tidak merusak layout */
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI DATA ANTI-GAGAL (FAIL-SAFE) ---
@st.cache_data(ttl=600)
def load_data():
    """Mencoba baca SQL dulu, jika gagal/error, langsung baca Excel agar web tidak pernah mati"""
    try:
        conn = sqlite3.connect('database_lahan.db')
        df = pd.read_sql_query("SELECT * FROM titik_acuan", conn)
        conn.close()
    except:
        try:
            # Fallback ke Excel langsung
            df = pd.read_excel('Data_Kesesuaian.xlsx')
            # Memperbaiki Merge Cell otomatis
            if 'Lat' in df.columns and 'Lon' in df.columns:
                df['Lat'] = df['Lat'].ffill()
                df['Lon'] = df['Lon'].ffill()
        except:
            return pd.DataFrame() # Jika Excel juga tidak ada
            
    # Bersihkan baris yang tidak ada koordinatnya
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
# HALAMAN 1: BERANDA (BERSIH & ELEGAN)
# ==========================================
if st.session_state.page == 'beranda':
    # Menggunakan banner gambar asli yang tidak merusak teks
    st.image("https://images.unsplash.com/photo-1595841696677-6489ff3f8cd1?q=80&w=1200&auto=format&fit=crop", use_container_width=True)
    
    st.markdown("<h1 style='text-align: center; padding-top: 20px;'>Sistem Informasi Spasial Lahan Kentang</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: gray;'>Platform Prediksi Kesesuaian Lahan Berbasis Agroklimat & Sebaran Hara</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Tombol Navigasi Simpel di Tengah Layar
    col_kosong1, col_btn1, col_btn2, col_kosong2 = st.columns([1, 2, 2, 1])
    with col_btn1:
        if st.button("🗺️ Peta Kesesuaian Lahan", use_container_width=True):
            st.session_state.page = 'fitur_peta'
            st.rerun()
    with col_btn2:
        if st.button("🌱 Rekomendasi Pemupukan", use_container_width=True):
            st.session_state.page = 'fitur_pupuk'
            st.rerun()

# ==========================================
# HALAMAN 2: PETA KESESUAIAN
# ==========================================
elif st.session_state.page == 'fitur_peta':
    
    # Navigasi Atas
    col_judul, col_kembali = st.columns([4, 1])
    with col_judul:
        st.title("Pemetaan Kesesuaian Lahan")
    with col_kembali:
        st.write("") # Spacer
        if st.button("🔙 Kembali ke Beranda", use_container_width=True):
            st.session_state.page = 'beranda'
            st.rerun()
            
    st.markdown("---")

    # Layout Kiri (Input) & Kanan (Peta)
    col_input, col_peta = st.columns([1, 2.5])
    
    with col_input:
        st.subheader("Parameter Analisis")
        radius_km = st.slider("Radius Batas Toleransi (Km)", 1.0, 15.0, 3.0, 0.5)
        ph_manual = st.number_input("Input pH (Opsional)", 0.0, 14.0, 0.0, 0.1)
        
        st.write("")
        if not df_data.empty:
            st.success(f"✅ Data Siap: {len(df_data)} titik observasi")
        else:
            st.error("❌ Data tidak ditemukan. Pastikan file Excel/DB ada.")
            
    with col_peta:
        # Peta Google Satellite
        m = folium.Map(
            location=[-7.2106, 109.8941], 
            zoom_start=9, 
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
            attr='Google Maps'
        )
        
        # Plot Data Titik (Dengan Garis Tepi Putih agar Sangat Terlihat)
        if not df_data.empty:
            for _, row in df_data.iterrows():
                kategori = str(row.get('Kecocokan', '')).strip().lower()
                
                # Warna solid
                if kategori == 'cocok': warna = '#00FF00' # Hijau
                elif kategori == 'netral': warna = '#FFFF00' # Kuning
                else: warna = '#FF0000' # Merah

                ph_tanah = row.get('PH_S1', 'N/A')
                elev = row.get('Elevasi', 'N/A')
                
                popup_text = f"<b>{kategori.upper()}</b><br>Elevasi: {elev} mdpl<br>pH: {ph_tanah}"
                
                folium.CircleMarker(
                    location=[row['Lat'], row['Lon']],
                    radius=7, 
                    color='white', # Garis tepi putih tegas
                    weight=2, 
                    fill=True, 
                    fill_color=warna, 
                    fill_opacity=1.0,
                    popup=folium.Popup(popup_text, max_width=200)
                ).add_to(m)

        # Plot Pin Biru Lokasi Klik Pengguna
        if st.session_state.clicked_lat is not None:
            folium.Marker(
                location=[st.session_state.clicked_lat, st.session_state.clicked_lon],
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
            
        # Render Peta
        map_interaction = st_folium(m, use_container_width=True, height=500, returned_objects=["last_clicked"])

    # Tangkap Koordinat Klik
    if map_interaction and map_interaction.get("last_clicked"):
        lat_klik = map_interaction["last_clicked"]["lat"]
        lon_klik = map_interaction["last_clicked"]["lng"]
        
        if st.session_state.clicked_lat != lat_klik or st.session_state.clicked_lon != lon_klik:
            st.session_state.clicked_lat = lat_klik
            st.session_state.clicked_lon = lon_klik
            st.rerun()

    # --- HASIL PREDIKSI (DI BAWAH PETA) ---
    if st.session_state.clicked_lat is not None:
        st.markdown("---")
        st.subheader("Hasil Evaluasi Lokasi")
        
        lat_eval = st.session_state.clicked_lat
        lon_eval = st.session_state.clicked_lon
        
        # Tampilkan Koordinat Langsung
        st.write(f"**Titik Terpilih:** {lat_eval:.5f}, {lon_eval:.5f}")
        
        with st.spinner("Menarik data satelit dan menghitung jarak..."):
            elevasi_satelit = get_elevation(lat_eval, lon_eval)
            
            if not df_data.empty and elevasi_satelit is not None:
                st.write(f"**Elevasi Lokasi:** {elevasi_satelit:.1f} mdpl")
                
                df_working = df_data.copy()
                df_working['Jarak_Km'] = df_working.apply(lambda r: hitung_jarak_haversine(lat_eval, lon_eval, r['Lat'], r['Lon']), axis=1)
                df_terfilter = df_working[df_working['Jarak_Km'] <= radius_km]
                
                if df_terfilter.empty:
                    st.error(f"⚠️ **DI LUAR JANGKAUAN:** Tidak ditemukan titik acuan dalam radius {radius_km} km.")
                else:
                    elev_min, elev_max = df_terfilter['Elevasi'].min(), df_terfilter['Elevasi'].max()
                    
                    if elevasi_satelit < (elev_min - 50.0) or elevasi_satelit > (elev_max + 50.0):
                        st.error(f"🟥 **TIDAK COCOK:** Ketinggian melampaui batas wilayah terdekat (Rentang Wajar: {elev_min:.0f} - {elev_max:.0f} mdpl).")
                    else:
                        hitung_suara = df_terfilter['Kecocokan'].str.lower().value_counts()
                        
                        if len(hitung_suara) > 1 and hitung_suara.iloc[0] == hitung_suara.iloc[1]:
                            st.warning(f"🟨 **NETRAL:** Karakteristik data acuan seimbang (50:50).")
                        else:
                            suara_dominan = hitung_suara.idxmax()
                            if suara_dominan == 'cocok':
                                st.success(f"🟩 **COCOK:** Mayoritas observasi di sekitar lokasi ini merekomendasikan penanaman.")
                            elif suara_dominan == 'netral':
                                st.warning(f"🟨 **NETRAL:** Zonasi di sekitar lokasi didominasi karakteristik lahan marginal.")
                            else:
                                st.error(f"🟥 **TIDAK COCOK:** Mayoritas observasi historis tidak merekomendasikan.")
            else:
                st.error("Gagal menarik data elevasi dari satelit.")

# ==========================================
# HALAMAN 3: REKOMENDASI PEMUPUKAN
# ==========================================
elif st.session_state.page == 'fitur_pupuk':
    col_judul, col_kembali = st.columns([4, 1])
    with col_judul:
        st.title("Rekomendasi Pemupukan")
    with col_kembali:
        st.write("")
        if st.button("🔙 Kembali ke Beranda", use_container_width=True):
            st.session_state.page = 'beranda'
            st.rerun()
            
    st.markdown("---")
    st.info("Modul kalkulasi nutrisi tanah sedang dipersiapkan.")