-- =========================================================
-- DATABASE: ai_papers
-- Multi-Agent AI Papers Management System
-- MySQL 8.0+
-- =========================================================
DROP DATABASE IF EXISTS ai_papers;
CREATE DATABASE ai_papers CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_papers;

-- 1. Table: users
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    noti_daily BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table: papers 
CREATE TABLE papers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    external_id VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    abstract TEXT NOT NULL,
    summary_en TEXT,
    summary_vi TEXT,
    authors JSON NOT NULL,
    pdf_url VARCHAR(500),
    pdf_path VARCHAR(255),
    published DATE NOT NULL,
    score FLOAT DEFAULT 0.0,
    has_audio BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Table: audio_abstracts
CREATE TABLE audio_abstracts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    paper_id BIGINT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    duration_seconds INT NOT NULL DEFAULT 0,
    paper_timestamps JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

-- 4. Table: digests
CREATE TABLE digests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. Table: digest_papers
CREATE TABLE digest_papers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    digest_id BIGINT NOT NULL,
    paper_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (digest_id) REFERENCES digests(id) ON DELETE CASCADE,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    UNIQUE(digest_id, paper_id)
);

-- 6. Table: chat_sessions
CREATE TABLE chat_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    paper_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

-- 7. Table: chat_messages (No audio file attached)
CREATE TABLE chat_messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    sources_json JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

-- 8. Table: topics
CREATE TABLE topics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    keywords_json JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 9. Table: paper_topics
CREATE TABLE paper_topics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    paper_id BIGINT NOT NULL,
    topic_id BIGINT NOT NULL,
    confidence_score FLOAT DEFAULT 0.0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
    UNIQUE(paper_id, topic_id),
    CHECK (confidence_score >= 0 AND confidence_score <= 1)
);
