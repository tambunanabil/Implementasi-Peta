-- ============================================================
-- JALANKAN SCRIPT INI SEKALI DI DATABASE MySQL
-- Host   : 153.92.15.9
-- DB     : u160973994_ilahan
-- User   : u160973994_ilahan
-- ============================================================

USE u160973994_ilahan;

-- Buat tabel titik_acuan jika belum ada
CREATE TABLE IF NOT EXISTS titik_acuan (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    Kabupaten   VARCHAR(100),
    Desa        VARCHAR(100),
    Lat         DOUBLE NOT NULL,
    Lon         DOUBLE NOT NULL,
    Elevasi     DOUBLE,
    PH_S1       DOUBLE,
    EC_S        DOUBLE,
    N_S         DOUBLE,
    P_S         DOUBLE,
    K_S         DOUBLE,
    Moist_S     DOUBLE,
    Temp_D_S    DOUBLE,
    N_Lab       DOUBLE,
    P_Lab       DOUBLE,
    K_Lab       DOUBLE,
    Status      VARCHAR(50),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Index untuk mempercepat query spasial
CREATE INDEX IF NOT EXISTS idx_lat_lon ON titik_acuan (Lat, Lon);
CREATE INDEX IF NOT EXISTS idx_status  ON titik_acuan (Status);
