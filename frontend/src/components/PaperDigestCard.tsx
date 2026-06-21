import React from 'react';
import { Link } from 'react-router-dom';
import type { DigestEntry } from '../types/digest';
import { arxivAbsUrl, hfPaperUrl } from '../utils/mediaUrl';
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
  const hfUrl = hfPaperUrl(paper.arxiv_id);

  return (
    <article className={`digest-card ${rank_position === 1 ? 'digest-card--top' : ''}`}>
      {/* Rank badge + score */}
      <div className="digest-card__header">
        <span className={`rank-badge ${rankClass}`}>
          {rank_position === 1 ? '🏆\u00A0' : rank_position === 2 ? '🥈\u00A0' : rank_position === 3 ? '🥉\u00A0' : ''}#{rank_position}
        </span>
        <span className="score-chip">
          👍 {paper.upvotes} upvotes
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
      <div className="digest-card__footer" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <a
          href={hfUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-paper-link btn-paper-link--hf"
          style={{
            background: '#fef3c7',
            color: '#d97706',
            borderColor: '#fde68a',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            border: '1px solid #fde68a',
            fontWeight: 500
          }}
        >
          🤗 Xem trên HuggingFace
        </a>
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
