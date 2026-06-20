import React from 'react';
import type { Topic } from '../../types/trend';

interface TrendBarChartProps {
  topics: Topic[];
  selectedTopicId: number | null;
  onSelectTopic: (topicId: number) => void;
}

export const TrendBarChart: React.FC<TrendBarChartProps> = ({
  topics,
  selectedTopicId,
  onSelectTopic,
}) => {
  // Find maximum paper count to calculate relative percentages
  const maxPaperCount = topics.reduce((max, t) => (t.paper_count > max ? t.paper_count : max), 0);

  if (topics.length === 0) {
    return (
      <div className="trend-chart-empty">
        <p>Không có dữ liệu biểu đồ.</p>
      </div>
    );
  }

  return (
    <div className="trend-bar-chart">
      <h3 className="trend-chart-title">📊 Phân bổ Bài báo theo Chủ đề</h3>
      <div className="trend-chart-bars">
        {topics.map((topic) => {
          const percentage = maxPaperCount > 0 ? (topic.paper_count / maxPaperCount) * 100 : 0;
          const isSelected = topic.id === selectedTopicId;

          return (
            <div
              key={topic.id}
              className={`trend-chart-row ${isSelected ? 'trend-chart-row--selected' : ''}`}
              onClick={() => onSelectTopic(topic.id)}
            >
              <div className="trend-chart-label">
                <span className="trend-topic-name" title={topic.name}>
                  {topic.name}
                </span>
                <span className="trend-topic-count">{topic.paper_count} bài báo</span>
              </div>
              <div className="trend-bar-container">
                <div
                  className="trend-bar-fill"
                  style={{ width: `${Math.max(percentage, 2)}%` }} // Minimum 2% width so it's always visible
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TrendBarChart;
