USE ai_papers;

-- Insert a demo user (password is 'password123' hashed using bcrypt)
INSERT IGNORE INTO users (id, email, password_hash, name, receive_emails, created_at)
VALUES (
    1,
    'demo_user@example.com',
    '$2b$12$Z/l9lB76vO54x1eN0nN3Q.FfK8ZqH0PZkWmF9vGZ0.vRz4eY5yYyG', -- bcrypt hash of 'password123'
    'Nguyen Van A',
    1,
    NOW()
);

-- Insert a demo paper metadata
INSERT IGNORE INTO papers (id, arxiv_id, title, authors, publish_date, abstract, summary, pdf_path, audio_path, status, created_at)
VALUES (
    1,
    '1706.03762',
    'Attention Is All You Need',
    'Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin',
    '2017-06-12',
    'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...',
    '### Tóm tắt chính\n- Giới thiệu mô hình Transformer đột phá dựa hoàn toàn trên cơ chế Attention, loại bỏ mạng nơ-ron tuần hoàn (RNN) truyền thống.\n- Đạt hiệu quả huấn luyện vượt trội và khả năng dịch máy song song hóa tốt.',
    './data/paper_pdf/1706.03762.pdf',
    './data/audio_abstract/1706.03762.mp3',
    'summarized',
    NOW()
);
