import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import numpy as np

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Informasi Geografis Lahan Kentang", layout="wide", initial_sidebar_state="collapsed")

# Inisialisasi Memori untuk menyimpan koordinat klik pengguna
if 'clicked_lat' not in st.session_state:
    st.session_state.clicked_lat = None
    st.session_state.clicked_lon = None

# --- 2. CUSTOM CSS: MINIMALIS, BERSIH, DAN PROFESIONAL (TANPA IKON RAMAI) ---
st.markdown("""
    <style>
    /* Menyembunyikan Sidebar Bawaan secara Total */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Latar Belakang Bernuansa Pertanian Teduh / Polos Elegan */
    .stApp {
        background-color: #f4f6f0;
    }
    
    /* Panel Konten Utama yang Solid, Bersih, dan Tegas seperti Web Asli */
    .block-container {
        background-color: #ffffff;
        padding: 3rem 4rem !important;
        border-radius: 0px; /* Menghilangkan sudut tumpul agar terkesan kaku formal */
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        max-width: 1200px;
        margin: auto;
    }

    /* Mengubah Gaya Tab Navigasi Atas agar Minimalis & Elegan */
    .stTabs [data-baseweb="tab-list"] {
        gap: 40px;
        background-color: transparent; /* Menghilangkan warna latar kotak navigasi */
        border-bottom: 2px solid #e0e0e0;
        padding: 0px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #666666 !important;
        font-weight: 500;
        font-size: 16px;
        background-color: transparent;
        padding: 12px 4px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        color: #1b4332 !important; /* Warna Hijau Tua untuk Tab Aktif */
        font-weight: 700;
        border-bottom: 3px solid #1b4332 !important;
    }

    /* Kotak Dasbor Hasil Analisis murni teks dan batas minimalis */
    div[data-testid="metric-container"] {
        background-color: #fafafa;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI LOGIKA SISTEM ---
@st.cache_data(ttl=600)
def query_database():
    try:
        conn = sqlite3.connect('database_lahan.db')
        df = pd.read_sql_query("SELECT * FROM titik_acuan", conn)
        conn.close()
        # Membersihkan data dari sel koordinat yang kosong
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

# --- 4. HEADER MINIMALIS ---
st.title("Sistem Informasi Geografis Lahan Kentang")
st.markdown("Analisis Spasial Distribusi Hara Lahan dan Model Prediksi Kesesuaian Komoditas")
st.markdown("<br>", unsafe_allow_html=True)

# --- 5. NAVIGASI UTAMA (TABS TANPA IKON AI) ---
tab_home, tab_map, tab_pupuk = st.tabs(["Beranda", "Prediksi Kesesuaian Lahan", "Rekomendasi Pemupukan"])

# ==========================================
# MENUS 1: BERANDA (MINIMALIS SEPERTI CONTOH WEB ANDA)
# ==========================================
with tab_home:
    st.markdown("### Tentang Sistem")
    st.write(
        "Sistem ini dirancang untuk mengintegrasikan data spasial sebaran hara tanah "
        "di 12 sentra produksi kentang di Pulau Jawa guna memberikan prediksi kesesuaian "
        "lahan yang dapat dipahami secara terukur."
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Ilustrasi gambar pertanian yang bersih (Parameter borderRadius yang merusak sudah dibuang)
    st.image(
        "https://images.unsplash.com/photo-1595841696677-6489ff3f8cd1?q=80&w=1200&auto=format&fit=crop", 
        caption="Sentra Produksi Komoditas Kentang Dataran Tinggi", 
        use_container_width=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Petunjuk Penggunaan Fitur:")
    st.markdown(
        "1. **Prediksi Kesesuaian Lahan:** Masuk ke tab kedua untuk melakukan simulasi pemilihan "
        "lokasi lahan. Klik pada peta untuk mendapatkan estimasi kelayakan berdasarkan parameter agroklimat lokal.<br>"
        "2. **Rekomendasi Pemupukan:** Masuk ke tab ketiga untuk melihat optimasi kebutuhan dosis nutrisi tanah.",
        unsafe_allow_html=True
    )

# ==========================================
# MENUS 2: PETA KESESUAIAN LAHAN
# ==========================================
with tab_map:
    st.markdown("### Model Prediksi Spasial Lahan")
    st.write("Silakan tentukan parameter pencarian kemudian interaksi langsung dengan peta untuk menentukan titik uji.")
    st.markdown("<br>", unsafe_allow_html=True)

    col_kontrol, col_peta = st.columns([1, 3])

    with col_kontrol:
        st.markdown("##### Parameter Model")
        radius_km = st.slider("Radius Batas Analisis (Km)", 1.0, 10.0, 3.0, 0.5)
        ph_manual = st.number_input("Input Data pH Mandiri (Opsional)", 0.0, 14.0, 0.0, 0.1)
        
        st.markdown("---")
        if not df_data.empty:
            st.caption(f"Koneksi Basis Data: {len(df_data)} Objek Terhubung.")
        else:
            st.caption("Koneksi Basis Data: Tidak aktif.")

    with col_peta:
        # Peta Dasar bergaya bersih/minimalis (CartoDB Positron)
        m = folium.Map(location=[-7.5, 110.0], zoom_start=7, tiles="CartoDB positron")
        
        # Menggambar Sebaran Titik Historis (Sesuai Kategori Warna di Excel)
        if not df_data.empty:
            for _, row in df_data.iterrows():
                status_lahan = str(row.get('Status', '')).strip().lower()
                
                # Standar Warna Tegas Formal
                if status_lahan == 'cocok': 
                    warna_titik = '#2d6a4f'    # Hijau Konservatif
                elif status_lahan == 'netral': 
                    warna_titik = '#d4af37'    # Kuning Emas Redup
                else: 
                    warna_titik = '#b7094c'    # Merah Marun

                nilai_ph = row.get('PH_S1', 'N/A')
                
                popup_html = f"""
                <div style='font-family: sans-serif; font-size: 12px; line-height: 1.5;'>
                    <b>Kategori Lahan:</b> {status_lahan.upper()}<br>
                    <b>Elevasi Data:</b> {row.get('Elevasi', 'N/A')} mdpl<br>
                    <b>Nilai pH (S1):</b> {nilai_ph}
                </div>
                """
                
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=5, color=warna_titik, fill=True, fill_color=warna_titik, fill_opacity=0.8,
                    popup=folium.Popup(popup_html, max_width=200)
                ).add_to(m)

        # Menggambar Titik Interaktif Berdasarkan Klik Pengguna (Pin Biru)
        if st.session_state.clicked_lat is not None:
            folium.Marker(
                location=[st.session_state.clicked_lat, st.session_state.clicked_lon],
                icon=folium.Icon(color='blue', icon='info-sign'),
                popup="Titik Evaluasi Pilihan Anda"
            ).add_to(m)
        
        # Tampilkan Peta ke Layar
        map_data = st_folium(m, width=900, height=480, returned_objects=["last_clicked"])

    # Logika Menangkap Klik Peta dan Memperbarui Posisi Marker Secara Instan
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        
        if st.session_state.clicked_lat != lat or st.session_state.clicked_lon != lon:
            st.session_state.clicked_lat = lat
            st.session_state.clicked_lon = lon
            st.rerun()

    # --- PANEL EVALUASI HASIL KLIK ---
    if st.session_state.clicked_lat is not None:
        lat = st.session_state.clicked_lat
        lon = st.session_state.clicked_lon
        
        st.markdown("---")
        st.markdown("### Ringkasan Analisis Lokasi")
        
        with st.spinner("Mengalkulasi koordinat spasial..."):
            elevasi_uji = get_elevation(lat, lon)
            
            # Layout Tiga Kotak Dasbor Bersih
            met1, met2, met3 = st.columns(3)
            met1.metric("Koordinat Lokasi", f"{lat:.4f}, {lon:.4f}")
            met2.metric("Ketinggian Wilayah (Satelit)", f"{elevasi_uji:.1f} mdpl" if elevasi_uji else "N/A")
            
            status_final, alasan = "MEMPROSES...", ""
            
            if not df_data.empty and elevasi_uji is not None:
                df_temp = df_data.copy()
                df_temp['Jarak_Km'] = df_temp.apply(lambda r: hitung_jarak_haversine(lat, lon, r['Latitude'], r['Longitude']), axis=1)
                df_terdekat = df_temp[df_temp['Jarak_Km'] <= radius_km]
                
                if df_terdekat.empty:
                    status_final, alasan = "DI LUAR JANGKAUAN", f"Tidak ditemukan parameter acuan dalam batas radius {radius_km} km."
                else:
                    elev_min, elev_max = df_terdekat['Elevasi'].min(), df_terdekat['Elevasi'].max()
                    if elevasi_uji < (elev_min - 50.0) or elevasi_uji > (elev_max + 50.0):
                        status_final, alasan = "TIDAK COCOK", f"Ketinggian lokasi ({elevasi_uji:.1f} mdpl) berada di luar rentang agroklimat wilayah sampel terdekat ({elev_min:.0f}-{elev_max:.0f} mdpl)."
                    else:
                        jumlah_status = df_terdekat['Status'].str.lower().value_counts()
                        if len(jumlah_status) > 1 and jumlah_status.iloc[0] == jumlah_status.iloc[1]:
                            status_final, alasan = "NETRAL", "Karakteristik tanah di sekitar titik uji memiliki sebaran nilai kesesuaian yang seimbang (50:50)."
                        else:
                            status_dominan = jumlah_status.idxmax()
                            if status_dominan == "cocok": 
                                status_final, alasan = "COCOK", "Mayoritas data historis spasial terdekat memenuhi klasifikasi kelayakan."
                            elif status_dominan == "netral": 
                                status_final, alasan = "NETRAL", "Zonasi data terdekat didominasi oleh klasifikasi lahan netral."
                            else: 
                                status_final, alasan = "TIDAK COCOK", "Mayoritas parameter observasi terdekat menunjukkan indikasi ketidakcocokan lahan."
            else:
                alasan = "Gagal memproses verifikasi spasial."
            
            met3.metric("Hasil Evaluasi", status_final)
            
            # Tampilan Kesimpulan Akhir dengan Alert Box Resmi Bawaan Streamlit
            if status_final == "COCOK": 
                st.success(f"**Kesimpulan:** Lahan Potensial. {alasan}")
            elif status_final == "NETRAL": 
                st.warning(f"**Kesimpulan:** Lahan Netral / Butuh Perlakuan Khusus. {alasan}")
            elif status_final == "TIDAK COCOK": 
                st.error(f"**Kesimpulan:** Lahan Tidak Direkomendasikan. {alasan}")
            else: 
                st.info(f"**Informasi:** {alasan}")

# ==========================================
# MENUS 3: REKOMENDASI PEMUPUKAN
# ==========================================
with tab_pupuk:
    st.markdown("### Dasbor Optimasi Kebutuhan Pupuk")
    st.info("Modul kalkulasi nutrisi berbasis parameter tanah sedang dipersiapkan untuk integrasi.")