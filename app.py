import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import numpy as np

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Informasi Lahan Kentang", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CUSTOM CSS: TEMA PERTANIAN ELEGAN & LATAR BELAKANG ---
st.markdown("""
    <style>
    /* Menyembunyikan Sidebar secara total */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Menambahkan Latar Belakang Gambar Pertanian */
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1595841696677-6489ff3f8cd1?q=80&w=1200&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }
    
    /* Memberikan latar belakang semi-transparan pada area konten agar teks tetap terbaca */
    .block-container {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 2rem !important;
        border-radius: 10px;
        margin-top: 2rem;
    }

    /* Tampilan Tab Navigasi Atas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: #1b4332;
        padding: 10px 20px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
        font-weight: 600;
        font-size: 16px;
        background-color: transparent;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        color: #d4af37 !important;
        border-bottom: 3px solid #d4af37 !important;
    }

    /* Kotak Dasbor Metrik */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border-left: 5px solid #2d6a4f;
        padding: 15px;
        border-radius: 6px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI UTAMA ---
@st.cache_data(ttl=600)
def query_database():
    try:
        conn = sqlite3.connect('database_lahan.db')
        df = pd.read_sql_query("SELECT * FROM titik_acuan", conn)
        conn.close()
        # Proteksi ganda agar peta tidak crash jika masih ada baris kosong
        df = df.dropna(subset=['Latitude', 'Longitude'])
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

# --- 4. HEADER UTAMA WEB ---
st.title("Sistem Spasial Prediksi Kesesuaian Lahan")
st.markdown("Analisis komparatif agroklimat dan distribusi hara untuk budidaya komoditas kentang.")
st.markdown("---")

# --- 5. NAVIGASI UTAMA (TABS) ---
tab1, tab2 = st.tabs(["Peta Kesesuaian Lahan", "Rekomendasi Pemupukan"])

# ==========================================
# TAB 1: PETA KESESUAIAN LAHAN
# ==========================================
with tab1:
    col_kontrol, col_peta = st.columns([1, 3])

    with col_kontrol:
        st.write("### Parameter Analisis")
        radius_km = st.slider("Radius Analisis Wilayah (Km)", 1.0, 10.0, 3.0, 0.5)
        ph_manual = st.number_input("Input pH Lokal (Opsional)", 0.0, 14.0, 0.0, 0.1)
        
        st.markdown("---")
        if not df_data.empty:
            st.caption(f"Status Sistem: {len(df_data)} titik observasi aktif.")
        else:
            st.caption("Status Sistem: Koneksi data tidak aktif.")

    with col_peta:
        m = folium.Map(location=[-7.5, 110.0], zoom_start=7, tiles="CartoDB positron")
        
        if not df_data.empty:
            for _, row in df_data.iterrows():
                status_lahan = str(row.get('Status', '')).strip().lower()
                
                if status_lahan == 'cocok': warna_titik = '#2d6a4f'
                elif status_lahan == 'netral': warna_titik = '#d4af37'
                else: warna_titik = '#b7094c'

                popup_html = f"""
                <div style='font-family: sans-serif; font-size: 12px;'>
                    <b>Kategori Lahan:</b> {status_lahan.upper()}<br>
                    <b>Elevasi:</b> {row.get('Elevasi', 'N/A')} mdpl<br>
                    <b>Kondisi pH:</b> {row.get('pH', 'N/A')}
                </div>
                """
                
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=5, color=warna_titik, fill=True, fill_color=warna_titik, fill_opacity=0.8,
                    popup=folium.Popup(popup_html, max_width=200)
                ).add_to(m)
        
        map_data = st_folium(m, width=900, height=480, returned_objects=["last_clicked"])

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        
        st.markdown("---")
        st.write("### Dasbor Hasil Analisis Titik")
        
        with st.spinner("Menghitung model spasial..."):
            elevasi_uji = get_elevation(lat, lon)
            
            met1, met2, met3 = st.columns(3)
            met1.metric("Koordinat Lokasi", f"{lat:.4f}, {lon:.4f}")
            met2.metric("Ketinggian Tanah", f"{elevasi_uji:.1f} mdpl" if elevasi_uji else "N/A")
            
            status_final, alasan = "MEMPROSES...", ""
            
            if not df_data.empty and elevasi_uji is not None:
                df_temp = df_data.copy()
                df_temp['Jarak_Km'] = df_temp.apply(lambda r: hitung_jarak_haversine(lat, lon, r['Latitude'], r['Longitude']), axis=1)
                df_terdekat = df_temp[df_temp['Jarak_Km'] <= radius_km]
                
                if df_terdekat.empty:
                    status_final, alasan = "DI LUAR JANGKAUAN", f"Tidak ditemukan titik acuan dalam batas radius {radius_km} km."
                else:
                    elev_min, elev_max = df_terdekat['Elevasi'].min(), df_terdekat['Elevasi'].max()
                    if elevasi_uji < (elev_min - 50.0) or elevasi_uji > (elev_max + 50.0):
                        status_final, alasan = "TIDAK COCOK", f"Ketinggian lokasi ({elevasi_uji:.1f} mdpl) tidak ideal dibandingkan dengan rentang historis wilayah ini ({elev_min:.0f}-{elev_max:.0f} mdpl)."
                    else:
                        jumlah_status = df_terdekat['Status'].str.lower().value_counts()
                        if len(jumlah_status) > 1 and jumlah_status.iloc[0] == jumlah_status.iloc[1]:
                            status_final, alasan = "NETRAL", "Kondisi historis lahan sekitar menunjukkan karakteristik yang seimbang antara parameter cocok dan tidak cocok."
                        else:
                            status_dominan = jumlah_status.idxmax()
                            if status_dominan == "cocok": 
                                status_final, alasan = "COCOK", "Berdasarkan mayoritas data historis spasial terdekat, lokasi ini memenuhi syarat."
                            elif status_dominan == "netral": 
                                status_final, alasan = "NETRAL", "Mayoritas zonasi sekitar berada pada kategori netral."
                            else: 
                                status_final, alasan = "TIDAK COCOK", "Mayoritas data observasi terdekat tidak menyarankan budidaya di titik ini."
            else:
                alasan = "Gagal memproses kalkulasi spasial."
            
            met3.metric("Hasil Prediksi", status_final)
            
            if status_final == "COCOK": st.success(f"**Kesimpulan:** Lahan Potensial. {alasan}")
            elif status_final == "NETRAL": st.warning(f"**Kesimpulan:** Lahan Marginal / Netral. {alasan}")
            elif status_final == "TIDAK COCOK": st.error(f"**Kesimpulan:** Lahan Tidak Direkomendasikan. {alasan}")
            else: st.info(f"**Informasi:** {alasan}")

# ==========================================
# TAB 2: REKOMENDASI PEMUPUKAN
# ==========================================
with tab2:
    st.write("### Dasbor Optimasi Pemupukan")
    st.info("Modul kalkulasi nutrisi dan dosis rekomendasi pupuk sedang dipersiapkan untuk integrasi sistem.")