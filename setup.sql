-- ============================================================
--  Kinetic Campus — MySQL Setup Script
--  Compatible with both the original Java project and the
--  new Python Flask application.
-- ============================================================

CREATE DATABASE IF NOT EXISTS kinetic_db;
USE kinetic_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) DEFAULT NULL,
    email     VARCHAR(100) NOT NULL UNIQUE,
    password  VARCHAR(255) NOT NULL,
    role      ENUM('user', 'admin') DEFAULT 'user'
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(255) DEFAULT NULL,
    event_date   DATE         DEFAULT NULL,
    semester     VARCHAR(50)  DEFAULT NULL,
    purpose      TEXT         DEFAULT NULL,
    outcome      TEXT         DEFAULT NULL,
    location     VARCHAR(255) DEFAULT NULL,
    capacity     INT          DEFAULT NULL,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    created_by   INT          DEFAULT NULL,
    join_count   INT          DEFAULT 0,
    banner_image VARCHAR(500) DEFAULT NULL,
    INDEX (created_by)
);

-- Event Registrations table
-- NOTE: Added 'department' column required by RegisterEventServlet / register_event route
CREATE TABLE IF NOT EXISTS event_registrations (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    event_id          INT          DEFAULT NULL,
    student_name      VARCHAR(255) DEFAULT NULL,
    semester          VARCHAR(100) DEFAULT NULL,
    department        VARCHAR(255) DEFAULT NULL,
    section           VARCHAR(100) DEFAULT NULL,
    university_id     VARCHAR(50)  DEFAULT NULL,
    registration_date TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    event_id   INT          DEFAULT NULL,
    message    VARCHAR(255) DEFAULT NULL,
    is_read    TINYINT(1)   DEFAULT 0,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ── Optional: If you already have the old schema without 'department' ──
-- Run this once to add the missing column:
-- ALTER TABLE event_registrations ADD COLUMN department VARCHAR(255) DEFAULT NULL AFTER semester;
