import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import numpy as np

# --- 1. KONFIGURASI ---
st.set_page_config(page_title="AgriGIS | Prediksi Lahan", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .reportview-container { background: #f8f9fa; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e0e0e0;
        padding: 5% 10%; border-radius: 8px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .stButton>button { background-color: #1E4620; color: white; border-radius: 4px; font-weight: bold; width: 100%;}
    .stButton>button:hover { background-color: #2e7d32; color: white; border-color: #2e7d32; }
    [data-testid="stSidebar"] { background-color: #f1f8e9; }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNGSI SISTEM ---
@st.cache_data(ttl=600)
def query_database():
    try:
        conn = sqlite3.connect('database_lahan.db')
        df = pd.read_sql_query("SELECT * FROM titik_acuan", conn)
        conn.close()
        # Baris dropna telah dihapus karena database sudah diperbaiki dari akarnya
        return df
    except Exception:
        return pd.DataFrame()

def get_elevation(lat, lon):
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
    try:
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

df_data = query_database()

# --- 3. SIDEBAR NAVIGASI ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/628/628283.png", width=80)
st.sidebar.title("AgriGIS Menu")
menu = st.sidebar.radio("Pilih Modul:", ["🗺️ Prediksi Kesesuaian Lahan", "🌱 Rekomendasi Pemupukan"])
st.sidebar.markdown("---")
st.sidebar.caption("Sistem Informasi Geografis Distribusi Hara & Prediksi Kesesuaian Lahan Kentang - Jawa.")

# ==========================================
# MODUL 1: PREDIKSI KESESUAIAN LAHAN
# ==========================================
if menu == "🗺️ Prediksi Kesesuaian Lahan":
    st.title("Sistem Geospasial Kesesuaian Lahan Kentang")
    st.markdown("Pilih lokasi pada peta untuk memprediksi kecocokan lahan berdasarkan elevasi dan data spasial terdekat.")
    st.markdown("---")

    col_kontrol, col_peta = st.columns([1, 3])

    with col_kontrol:
        st.subheader("⚙️ Parameter Uji")
        radius_km = st.slider("Radius Pencarian (Km)", 1.0, 10.0, 3.0, 0.5)
        ph_manual = st.number_input("Input pH Tanah (Opsional)", 0.0, 14.0, 0.0, 0.1)
        
        st.markdown("---")
        st.markdown("**Status Database SQL:**")
        if not df_data.empty:
            st.success(f"✅ Terhubung: {len(df_data)} Titik")
        else:
            st.error("❌ Database Kosong/Terputus")

    with col_peta:
        m = folium.Map(location=[-7.5, 110.0], zoom_start=7, tiles="CartoDB positron")
        
        if not df_data.empty:
            for _, row in df_data.iterrows():
                status_lahan = str(row.get('Status', '')).strip().lower()
                
                if status_lahan == 'cocok': warna_titik = 'green'
                elif status_lahan == 'netral': warna_titik = 'orange'
                else: warna_titik = 'red'

                popup_html = f"<b>Status:</b> {status_lahan.upper()}<br><b>Elevasi:</b> {row.get('Elevasi', 'N/A')} mdpl<br><b>pH:</b> {row.get('pH', 'N/A')}"
                
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=5, color=warna_titik, fill=True, fill_opacity=0.7,
                    tooltip="Klik untuk detail", popup=folium.Popup(popup_html, max_width=200)
                ).add_to(m)
        
        map_data = st_folium(m, width=900, height=450, returned_objects=["last_clicked"])

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        
        st.markdown("---")
        st.subheader("📊 Hasil Analisis Geospasial")
        
        with st.spinner("Memproses algoritma spasial..."):
            elevasi_uji = get_elevation(lat, lon)
            
            met1, met2, met3 = st.columns(3)
            met1.metric("Koordinat Uji", f"{lat:.4f}, {lon:.4f}")
            met2.metric("Ketinggian Satelit", f"{elevasi_uji:.1f} mdpl" if elevasi_uji else "Gagal memuat API")
            
            status_final, alasan = "MEMPROSES...", ""
            
            if not df_data.empty and elevasi_uji is not None:
                df_temp = df_data.copy()
                df_temp['Jarak_Km'] = df_temp.apply(lambda r: hitung_jarak_haversine(lat, lon, r['Latitude'], r['Longitude']), axis=1)
                df_terdekat = df_temp[df_temp['Jarak_Km'] <= radius_km]
                
                if df_terdekat.empty:
                    status_final, alasan = "TIDAK ADA DATA", f"Tidak ada titik acuan dalam radius {radius_km} km."
                else:
                    elev_min, elev_max = df_terdekat['Elevasi'].min(), df_terdekat['Elevasi'].max()
                    if elevasi_uji < (elev_min - 50.0) or elevasi_uji > (elev_max + 50.0):
                        status_final, alasan = "TIDAK COCOK", f"Elevasi ({elevasi_uji:.1f} mdpl) di luar rentang wajar ({elev_min}-{elev_max} mdpl)."
                    else:
                        jumlah_status = df_terdekat['Status'].str.lower().value_counts()
                        if len(jumlah_status) > 1 and jumlah_status.iloc[0] == jumlah_status.iloc[1]:
                            status_final, alasan = "NETRAL", "Karakteristik titik acuan terdekat saling bertolak belakang (50:50)."
                        else:
                            status_dominan = jumlah_status.idxmax()
                            if status_dominan == "cocok": status_final, alasan = "COCOK", "Mayoritas titik acuan terdekat cocok."
                            elif status_dominan == "netral": status_final, alasan = "NETRAL", "Mayoritas titik acuan berstatus netral."
                            else: status_final, alasan = "TIDAK COCOK", "Mayoritas titik acuan tidak merekomendasikan."
            else:
                alasan = "Sistem gagal memproses data acuan/elevasi."
            
            met3.metric("Status Prediksi", status_final)
            
            if status_final == "COCOK": st.success(f"**Kesimpulan:** Direkomendasikan. {alasan}")
            elif status_final == "NETRAL": st.warning(f"**Kesimpulan:** Butuh Perlakuan. {alasan}")
            elif status_final == "TIDAK COCOK": st.error(f"**Kesimpulan:** Tidak Direkomendasikan. {alasan}")
            else: st.info(f"**Informasi:** {alasan}")

# ==========================================
# MODUL 2: REKOMENDASI PEMUPUKAN
# ==========================================
elif menu == "🌱 Rekomendasi Pemupukan":
    st.title("Sistem Rekomendasi Pemupukan")
    st.info("Modul kalkulasi dosis pemupukan sedang disiapkan untuk diintegrasikan.")
