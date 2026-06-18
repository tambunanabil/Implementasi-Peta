import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import numpy as np

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AgriGIS | Lahan Kentang", layout="wide", initial_sidebar_state="collapsed")

# Inisialisasi Memori untuk menyimpan titik klik pengguna
if 'clicked_lat' not in st.session_state:
    st.session_state.clicked_lat = None
    st.session_state.clicked_lon = None

# --- 2. CUSTOM CSS: TEMA PERTANIAN ELEGAN (DARKER BACKGROUND) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Latar Belakang Pertanian yang Lebih Gelap/Teduh */
    .stApp {
        background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.6)), url("https://images.unsplash.com/photo-1516253593875-bd7ba052fbc5?q=80&w=1200&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }
    
    /* Area Konten Putih Bersih (Lebih Solid agar tidak nabrak) */
    .block-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 2rem 3rem !important;
        border-radius: 12px;
        margin-top: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }

    /* Kotak Metrik */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border-left: 5px solid #2d6a4f;
        padding: 15px;
        border-radius: 6px;
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

# --- 4. NAVIGASI MENU UTAMA (TABS) ---
tab_home, tab_map, tab_pupuk = st.tabs(["🏠 Beranda Utama", "🗺️ Prediksi Kesesuaian Lahan", "🌱 Rekomendasi Pemupukan"])

# ==========================================
# MENU 1: BERANDA
# ==========================================
with tab_home:
    st.title("Sistem Informasi Geografis Lahan Kentang")
    st.subheader("Platform Analisis Spasial Distribusi Hara & Agroklimat")
    st.markdown("---")
    
    col_img, col_text = st.columns([1, 1.5])
    with col_img:
        st.image("https://images.unsplash.com/photo-1595841696677-6489ff3f8cd1?q=80&w=600&auto=format&fit=crop", borderRadius=10)
    with col_text:
        st.markdown("""
        ### Selamat Datang
        Aplikasi ini dirancang untuk memetakan dan memprediksi kesesuaian lahan bagi budidaya komoditas kentang di berbagai sentra di Pulau Jawa.
        
        **Fitur Utama:**
        1. **Prediksi Kesesuaian Lahan (Navigasi Tab 2):** Mengevaluasi titik lahan baru dengan membandingkan ketinggian (elevasi) dan data historis (`PH_S1` & Status) dari titik observasi terdekat.
        2. **Rekomendasi Pemupukan (Navigasi Tab 3):** *[Sedang dalam pengembangan]* Modul kalkulasi dosis nutrisi lahan.
        
        Silakan klik *Tab* di atas untuk memulai analisis.
        """)

# ==========================================
# MENU 2: PETA KESESUAIAN LAHAN
# ==========================================
with tab_map:
    st.title("Pemetaan & Prediksi Lokasi")
    st.markdown("Klik di area mana saja pada peta. Titik biru akan muncul, dan sistem akan mengalkulasi prediksi kecocokannya.")
    st.markdown("---")

    col_kontrol, col_peta = st.columns([1, 3])

    with col_kontrol:
        st.write("### Parameter")
        radius_km = st.slider("Radius Analisis (Km)", 1.0, 10.0, 3.0, 0.5)
        ph_manual = st.number_input("Input pH Lokal (Opsional)", 0.0, 14.0, 0.0, 0.1)
        
        st.markdown("---")
        if not df_data.empty:
            st.success(f"✅ Sistem Aktif: {len(df_data)} titik acuan terhubung.")
        else:
            st.error("❌ Database gagal dimuat.")

    with col_peta:
        # Peta Dasar
        m = folium.Map(location=[-7.5, 110.0], zoom_start=7, tiles="CartoDB positron")
        
        # 1. Menggambar Titik Acuan dari Database
        if not df_data.empty:
            for _, row in df_data.iterrows():
                # Memastikan spasi terhapus saat membaca status
                status_lahan = str(row.get('Status', '')).strip().lower()
                
                # Pewarnaan Kategori
                if status_lahan == 'cocok': warna_titik = '#2d6a4f' # Hijau
                elif status_lahan == 'netral': warna_titik = '#d4af37' # Emas/Kuning
                else: warna_titik = '#b7094c' # Merah

                # PERBAIKAN PH_S1
                nilai_ph = row.get('PH_S1', 'N/A')
                
                popup_html = f"""
                <div style='font-family: sans-serif; font-size: 12px;'>
                    <b>Kategori:</b> {status_lahan.upper()}<br>
                    <b>Elevasi:</b> {row.get('Elevasi', 'N/A')} mdpl<br>
                    <b>pH (S1):</b> {nilai_ph}
                </div>
                """
                
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=5, color=warna_titik, fill=True, fill_color=warna_titik, fill_opacity=0.8,
                    popup=folium.Popup(popup_html, max_width=200)
                ).add_to(m)

        # 2. Menggambar Titik Klik Pengguna (Warna Biru)
        if st.session_state.clicked_lat is not None:
            folium.Marker(
                location=[st.session_state.clicked_lat, st.session_state.clicked_lon],
                icon=folium.Icon(color='blue', icon='info-sign'),
                popup="Lokasi Uji (Klik Anda)"
            ).add_to(m)
        
        # Render Peta
        map_data = st_folium(m, width=900, height=480, returned_objects=["last_clicked"])

    # 3. Menangkap Klik Peta dan Memperbarui Titik Biru
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        
        # Jika koordinat baru berbeda dengan memori, simpan dan muat ulang peta agar titik tergambar
        if st.session_state.clicked_lat != lat or st.session_state.clicked_lon != lon:
            st.session_state.clicked_lat = lat
            st.session_state.clicked_lon = lon
            st.rerun()

    # --- PANEL HASIL PREDIKSI ---
    if st.session_state.clicked_lat is not None:
        lat = st.session_state.clicked_lat
        lon = st.session_state.clicked_lon
        
        st.markdown("---")
        st.write("### Dasbor Hasil Analisis Titik")
        
        with st.spinner("Menghitung model spasial..."):
            elevasi_uji = get_elevation(lat, lon)
            
            met1, met2, met3 = st.columns(3)
            met1.metric("Koordinat Lokasi Uji", f"{lat:.4f}, {lon:.4f}")
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
# MENU 3: REKOMENDASI PEMUPUKAN
# ==========================================
with tab_pupuk:
    st.write("### Dasbor Optimasi Pemupukan")
    st.info("Modul kalkulasi nutrisi dan dosis rekomendasi pupuk sedang dipersiapkan untuk integrasi sistem.")