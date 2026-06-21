import React from 'react';
import type { Topic } from '../../types/trend';

interface TopicListProps {
  topics: Topic[];
  selectedTopicId: number | null;
  onSelectTopic: (topicId: number) => void;
}

export const TopicList: React.FC<TopicListProps> = ({
  topics,
  selectedTopicId,
  onSelectTopic,
}) => {
  if (topics.length === 0) {
    return (
      <div className="topic-list-empty">
        <p>Không có danh sách chủ đề.</p>
      </div>
    );
  }

  return (
    <div className="topic-list-container">
      <h3 className="topic-list-title">🏷️ Danh sách Chủ đề</h3>
      <div className="topic-list-items">
        {topics.map((topic) => {
          const isSelected = topic.id === selectedTopicId;

          return (
            <div
              key={topic.id}
              className={`topic-list-item ${isSelected ? 'topic-list-item--selected' : ''}`}
              onClick={() => onSelectTopic(topic.id)}
            >
              <div className="topic-item-header">
                <h4 className="topic-item-name">{topic.name}</h4>
                <div className="topic-item-stats">
                  <span className="badge-papers">{topic.paper_count} bài</span>
                  {topic.confidence_avg > 0 && (
                    <span className="badge-confidence" title="Độ tin cậy trung bình của phân nhóm">
                      ★ {topic.confidence_avg}
                    </span>
                  )}
                </div>
              </div>
              
              {topic.description && (
                <p className="topic-item-desc">{topic.description}</p>
              )}

              {topic.keywords && topic.keywords.length > 0 && (
                <div className="topic-item-keywords">
                  {topic.keywords.map((kw, idx) => (
                    <span key={idx} className="keyword-chip">
                      #{kw}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TopicList;
