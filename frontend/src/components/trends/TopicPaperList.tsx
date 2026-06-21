import React from 'react';
import { Link } from 'react-router-dom';
import type { Topic } from '../../types/trend';
import { formatDate } from '../../utils/formatters';
import { externalAbsUrl } from '../../utils/mediaUrl';

interface TopicPaperListProps {
  topic: Topic | null;
}

export const TopicPaperList: React.FC<TopicPaperListProps> = ({ topic }) => {
  if (!topic) {
    return (
      <div className="topic-paper-empty">
        <span className="info-icon">👈</span>
        <p>Chọn một chủ đề ở danh sách bên trái để xem các bài báo liên quan.</p>
      </div>
    );
  }

  const papers = topic.papers || [];

  return (
    <div className="topic-paper-list">
      <div className="topic-paper-header">
        <h3>📚 Bài báo thuộc chủ đề: <span className="topic-highlight">{topic.name}</span></h3>
        <span className="badge-count">{papers.length} bài báo</span>
      </div>

      {papers.length === 0 ? (
        <div className="topic-paper-no-data">
          <p>Không có bài báo nào được gán cho chủ đề này.</p>
        </div>
      ) : (
        <div className="topic-papers-container">
          {papers.map((paper) => {
            // Check if external_id is present or try to extract it from typical title/abstract patterns (if any)
            const externalId = (paper as any).external_id;

            return (
              <div key={paper.id} className="trend-paper-card">
                <h4 className="trend-paper-title">{paper.title}</h4>
                
                <div className="trend-paper-meta">
                  {paper.published && (
                    <span className="trend-paper-date">
                      📅 Xuất bản: {formatDate(paper.published)}
                    </span>
                  )}
                  {externalId && (
                    <a
                      href={(paper as any).source_url || externalAbsUrl(externalId)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="arxiv-link"
                    >
                      🔗 Nguồn: {externalId}
                    </a>
                  )}
                </div>

                <p className="trend-paper-abstract">
                  {paper.abstract}
                </p>

                <div className="trend-paper-actions">
                  <Link to={`/papers/${paper.id}`} className="btn-view-paper-detail">
                    Xem chi tiết →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default TopicPaperList;
