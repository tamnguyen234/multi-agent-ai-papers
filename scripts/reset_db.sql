-- WARNING:
-- This script will DROP and recreate the ai_papers database.
-- Use only in local development.

DROP DATABASE IF EXISTS ai_papers;

CREATE DATABASE ai_papers
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Table: papers
CREATE TABLE papers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    external_id VARCHAR(50) NOT NULL UNIQUE,
    title TEXT NOT NULL,
    abstract_en TEXT NOT NULL,
    abstract_vi TEXT,
    authors TEXT,
    published DATE,
    source_url TEXT,
    pdf_path VARCHAR(500),
    source VARCHAR(100) NOT NULL,
    score FLOAT NOT NULL DEFAULT 0,
    has_audio BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_papers_external_id ON papers(external_id);
CREATE INDEX idx_papers_published ON papers(published);
CREATE INDEX idx_papers_score ON papers(score);
CREATE INDEX idx_papers_created_at ON papers(created_at);

-- 3. Table: digests
CREATE TABLE digests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    digest_date DATE NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Table: digest_papers
CREATE TABLE digest_papers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    digest_id BIGINT NOT NULL,
    paper_id BIGINT NOT NULL,
    rank_position INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_digest_papers_digest
        FOREIGN KEY (digest_id)
        REFERENCES digests(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_digest_papers_paper
        FOREIGN KEY (paper_id)
        REFERENCES papers(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_digest_paper
        UNIQUE (digest_id, paper_id),
    CONSTRAINT uq_digest_rank
        UNIQUE (digest_id, rank_position),
    CONSTRAINT chk_rank_position
        CHECK (rank_position BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_digest_papers_digest_id ON digest_papers(digest_id);
CREATE INDEX idx_digest_papers_paper_id ON digest_papers(paper_id);
CREATE INDEX idx_digest_papers_rank_position ON digest_papers(rank_position);

-- 5. Table: audio_abstracts
CREATE TABLE audio_abstracts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    paper_id BIGINT NOT NULL UNIQUE,
    file_path VARCHAR(500) NOT NULL,
    duration_seconds INT,
    paper_timestamps JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audio_abstracts_paper
        FOREIGN KEY (paper_id)
        REFERENCES papers(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Table: chat_sessions
CREATE TABLE chat_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    paper_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_sessions_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_chat_sessions_paper
        FOREIGN KEY (paper_id)
        REFERENCES papers(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_paper_id ON chat_sessions(paper_id);

-- 7. Table: chat_messages
CREATE TABLE chat_messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chat_session_id BIGINT NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_messages_session
        FOREIGN KEY (chat_session_id)
        REFERENCES chat_sessions(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_chat_messages_session_id ON chat_messages(chat_session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- 8. Table: topics
CREATE TABLE topics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    keywords_json JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Table: paper_topics
CREATE TABLE paper_topics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    paper_id BIGINT NOT NULL,
    topic_id BIGINT NOT NULL,
    confidence_score FLOAT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_paper_topics_paper
        FOREIGN KEY (paper_id)
        REFERENCES papers(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_paper_topics_topic
        FOREIGN KEY (topic_id)
        REFERENCES topics(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_paper_topic
        UNIQUE (paper_id, topic_id),
    CONSTRAINT chk_confidence_score
        CHECK (confidence_score >= 0 AND confidence_score <= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_paper_topics_paper_id ON paper_topics(paper_id);
CREATE INDEX idx_paper_topics_topic_id ON paper_topics(topic_id);

-- 10. Table: notifications
CREATE TABLE notifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    digest_id BIGINT NOT NULL,
    channel ENUM('email', 'web', 'system') NOT NULL DEFAULT 'email',
    status ENUM('pending', 'sent', 'failed') NOT NULL DEFAULT 'pending',
    sent_at DATETIME,
    error_message TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notifications_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_notifications_digest
        FOREIGN KEY (digest_id)
        REFERENCES digests(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_user_digest_channel
        UNIQUE (user_id, digest_id, channel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_digest_id ON notifications(digest_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_sent_at ON notifications(sent_at);
