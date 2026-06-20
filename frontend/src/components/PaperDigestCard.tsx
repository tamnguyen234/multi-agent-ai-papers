import React from 'react';
import { Link } from 'react-router-dom';
import type { DigestEntry } from '../types/digest';
import { formatScore, arxivAbsUrl } from '../utils/mediaUrl';
import AudioPlayer from './AudioPlayer';

interface PaperDigestCardProps {
  entry: DigestEntry;
}

const rankBadgeColors: Record<number, string> = {
  1: 'rank-gold',
  2: 'rank-silver',
  3: 'rank-bronze',
};

const PaperDigestCard: React.FC<PaperDigestCardProps> = ({ entry }) => {
  const { rank_position, paper } = entry;
  const audioSrc = paper.audio_abstract_url || paper.audio_abstract_path;
  const rankClass = rankBadgeColors[rank_position] || 'rank-default';
  const arxivUrl = arxivAbsUrl(paper.arxiv_id);
  const scoreLabel = formatScore(paper.score);

  return (
    <article className={`digest-card ${rank_position === 1 ? 'digest-card--top' : ''}`}>
      {/* Rank badge + score */}
      <div className="digest-card__header">
        <span className={`rank-badge ${rankClass}`}>
          {rank_position === 1 ? '🏆' : rank_position === 2 ? '🥈' : rank_position === 3 ? '🥉' : `#${rank_position}`}
          &nbsp;#{rank_position}
        </span>
        <span className="score-chip">
          ⭐ Score {scoreLabel}
        </span>
      </div>

      {/* Paper title */}
      <h3 className="digest-card__title">
        <Link to={`/papers/${paper.id}`}>
          {paper.title}
        </Link>
      </h3>

      {/* Meta: arxiv_id + published */}
      <div className="digest-card__meta">
        <span className="meta-tag">📄 {paper.arxiv_id}</span>
        {paper.published && (
          <span className="meta-tag">📅 {paper.published}</span>
        )}
        {paper.has_audio && (
          <span className="meta-tag meta-tag--audio">🎙️ Audio</span>
        )}
      </div>

      {/* Summary */}
      {paper.summary && (
        <p className="digest-card__summary">{paper.summary}</p>
      )}

      {/* Audio player */}
      {audioSrc && (
        <AudioPlayer
          src={audioSrc}
          title="Audio Abstract"
          durationSeconds={paper.audio_duration_seconds}
        />
      )}

      {/* Footer actions */}
      <div className="digest-card__footer">
        <a
          href={arxivUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-paper-link btn-paper-link--arxiv"
        >
          🔗 Xem trên arXiv
        </a>
      </div>
    </article>
  );
};

export default PaperDigestCard;
