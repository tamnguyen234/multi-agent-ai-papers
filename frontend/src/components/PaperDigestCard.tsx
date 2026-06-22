import React from 'react';
import { Link } from 'react-router-dom';
import type { DigestEntry } from '../types/digest';
import { externalAbsUrl } from '../utils/mediaUrl';
import { formatScore } from '../utils/formatters';
import AudioPlayer from './AudioPlayer';
import { Trophy, Medal, Award, TrendingUp, FileText, Calendar, Mic, ExternalLink } from 'lucide-react';

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
  const sourceUrl = externalAbsUrl(paper.external_id);
  const scoreLabel = formatScore(paper.score);

  return (
    <article className={`digest-card ${rank_position === 1 ? 'digest-card--top' : ''}`}>
      {/* Rank badge + score */}
      <div className="digest-card__header">
        <span className={`rank-badge ${rankClass}`}>
          {rank_position === 1 ? <Trophy size={14} className="mr-1" /> : rank_position === 2 ? <Medal size={14} className="mr-1" /> : rank_position === 3 ? <Award size={14} className="mr-1" /> : `#${rank_position}`}
          &nbsp;Rank {rank_position}
        </span>
        <span className="score-chip">
          <TrendingUp size={14} className="mr-1" /> Score {scoreLabel}
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
        <span className="meta-tag"><FileText size={14} className="mr-1" /> {paper.external_id}</span>
        {paper.published && (
          <span className="meta-tag"><Calendar size={14} className="mr-1" /> {paper.published}</span>
        )}
        {paper.has_audio && (
          <span className="meta-tag meta-tag--audio"><Mic size={14} className="mr-1" /> Audio Available</span>
        )}
      </div>

      {/* Summary */}
      {(paper.abstract_vi || paper.abstract_en) && (
        <p className="digest-card__summary">{paper.abstract_vi || paper.abstract_en}</p>
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
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-paper-link btn-paper-link--arxiv flex items-center gap-2"
        >
          <ExternalLink size={16} /> View Source
        </a>
      </div>
    </article>
  );
};

export default PaperDigestCard;
