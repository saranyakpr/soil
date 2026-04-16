-- ═══════════════════════════════════════════════════════════════════════
-- SOIL VISION 360 — MySQL Database Schema
-- Run this to initialize the database
-- ═══════════════════════════════════════════════════════════════════════

-- Create database
CREATE DATABASE IF NOT EXISTS soil_vision_360 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE soil_vision_360;

-- ─── USERS TABLE ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id           INT PRIMARY KEY AUTO_INCREMENT,
    name         VARCHAR(100) NOT NULL,
    email        VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role         ENUM('user', 'admin', 'analyst') DEFAULT 'user',
    api_key      VARCHAR(64) UNIQUE,
    is_active    BOOLEAN DEFAULT TRUE,
    last_login   DATETIME NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_api_key (api_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── SOIL REPORTS TABLE ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS soil_reports (
    id                   INT PRIMARY KEY AUTO_INCREMENT,
    soil_id              VARCHAR(30) NOT NULL UNIQUE,
    soil_type            VARCHAR(50) NOT NULL,
    soil_code            VARCHAR(10) NOT NULL,
    
    -- Color data
    avg_red              INT DEFAULT 0,
    avg_green            INT DEFAULT 0,
    avg_blue             INT DEFAULT 0,
    
    -- Core scores (0-100)
    water_retention      INT DEFAULT 0,
    crop_score           INT DEFAULT 0,
    construction_score   INT DEFAULT 0,
    heat_index           INT DEFAULT 0,
    
    -- Advanced analytics
    land_potential_score INT DEFAULT 0,
    agriculture_roi      DECIMAL(6,2) DEFAULT 0.00,
    construction_risk    VARCHAR(20) DEFAULT 'Low',
    flood_risk           VARCHAR(20) DEFAULT 'Low',
    
    -- Geospatial
    image_path           VARCHAR(255),
    district             VARCHAR(100),
    latitude             DECIMAL(10, 7),
    longitude            DECIMAL(10, 7),
    
    -- Relations
    user_id              INT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_soil_id (soil_id),
    INDEX idx_soil_type (soil_type),
    INDEX idx_district (district),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── DISTRICT SOIL DATA TABLE ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS district_soil_data (
    id                  INT PRIMARY KEY AUTO_INCREMENT,
    district_name       VARCHAR(100) NOT NULL UNIQUE,
    dominant_soil_type  VARCHAR(50),
    black_count         INT DEFAULT 0,
    red_count           INT DEFAULT 0,
    yellow_count        INT DEFAULT 0,
    brown_count         INT DEFAULT 0,
    total_analyses      INT DEFAULT 0,
    avg_land_potential  DECIMAL(6,2) DEFAULT 0.00,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_district (district_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── CLIMATE RECORDS TABLE ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS climate_records (
    id                  INT PRIMARY KEY AUTO_INCREMENT,
    district            VARCHAR(100) NOT NULL,
    year                INT NOT NULL,
    avg_rainfall_mm     DECIMAL(8,2) DEFAULT 0.00,
    avg_temp_celsius    DECIMAL(5,2) DEFAULT 0.00,
    drought_risk_index  DECIMAL(5,2) DEFAULT 0.00,
    flood_risk_index    DECIMAL(5,2) DEFAULT 0.00,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_district_year (district, year),
    INDEX idx_district_year (district, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── SEED DATA ────────────────────────────────────────────────────────────────

-- Default admin user (password: admin123)
INSERT IGNORE INTO users (name, email, password_hash, role, api_key, is_active)
VALUES (
    'Admin',
    'admin@soilvision360.com',
    'changeme:hashedpassword',  -- Will be overwritten by app startup
    'admin',
    'sv360-admin-api-key-000000000000000000000000000000',
    TRUE
);

-- Tamil Nadu districts
INSERT IGNORE INTO district_soil_data (district_name) VALUES
    ('Chennai'), ('Coimbatore'), ('Madurai'), ('Tiruchirappalli'), ('Salem'),
    ('Tirunelveli'), ('Vellore'), ('Erode'), ('Thoothukkudi'), ('Dindigul'),
    ('Thanjavur'), ('Ranipet'), ('Sivaganga'), ('Virudhunagar'), ('Namakkal'),
    ('Nagapattinam'), ('Tiruvallur'), ('Kancheepuram'), ('Cuddalore'), ('Villupuram'),
    ('Krishnagiri'), ('Dharmapuri'), ('Tiruppur'), ('Karur'), ('Perambalur'),
    ('Ariyalur'), ('Pudukkottai'), ('Ramanathapuram'), ('The Nilgiris'),
    ('Tiruvannamalai'), ('Kallakurichi'), ('Chengalpattu'), ('Tirupathur'), ('Mayiladuthurai');

-- Sample climate records for Tamil Nadu
INSERT IGNORE INTO climate_records (district, year, avg_rainfall_mm, avg_temp_celsius, drought_risk_index, flood_risk_index) VALUES
    ('Chennai',     2023, 1200.5, 29.3, 2.1, 4.5),
    ('Coimbatore',  2023, 680.2,  28.1, 3.4, 2.1),
    ('Madurai',     2023, 920.8,  30.5, 3.0, 3.2),
    ('Thanjavur',   2023, 1450.0, 28.8, 1.5, 5.8),
    ('The Nilgiris',2023, 2800.0, 18.5, 0.8, 6.2);

-- ─── VIEWS ────────────────────────────────────────────────────────────────────

-- View: Recent analyses with user info
CREATE OR REPLACE VIEW v_recent_analyses AS
SELECT 
    sr.id,
    sr.soil_id,
    sr.soil_type,
    sr.water_retention,
    sr.crop_score,
    sr.construction_score,
    sr.heat_index,
    sr.land_potential_score,
    sr.district,
    sr.created_at,
    u.name AS user_name,
    u.email AS user_email
FROM soil_reports sr
LEFT JOIN users u ON sr.user_id = u.id
ORDER BY sr.created_at DESC;

-- View: District analytics
CREATE OR REPLACE VIEW v_district_analytics AS
SELECT 
    d.district_name,
    d.dominant_soil_type,
    d.total_analyses,
    d.avg_land_potential,
    d.black_count,
    d.red_count,
    d.yellow_count,
    d.brown_count,
    COALESCE(cr.avg_rainfall_mm, 0) AS latest_rainfall,
    COALESCE(cr.avg_temp_celsius, 0) AS latest_temp,
    COALESCE(cr.flood_risk_index, 0) AS flood_risk
FROM district_soil_data d
LEFT JOIN climate_records cr ON d.district_name = cr.district AND cr.year = 2023;

-- ─── STORED PROCEDURES ───────────────────────────────────────────────────────

DELIMITER $$

-- Get soil type statistics
CREATE PROCEDURE IF NOT EXISTS GetSoilStats()
BEGIN
    SELECT 
        soil_type,
        COUNT(*) as total_count,
        AVG(water_retention) as avg_water_retention,
        AVG(crop_score) as avg_crop_score,
        AVG(construction_score) as avg_construction_score,
        AVG(land_potential_score) as avg_land_potential,
        MAX(created_at) as last_analyzed
    FROM soil_reports
    GROUP BY soil_type
    ORDER BY total_count DESC;
END$$

DELIMITER ;

-- ─── END OF SCHEMA ────────────────────────────────────────────────────────────