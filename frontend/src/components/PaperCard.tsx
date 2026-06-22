import React from 'react';
import { Link } from 'react-router-dom';
import type { Paper } from '../types/paper';
import { formatAuthorsShort, formatDate, formatScore, truncateText } from '../utils/formatters';
import { buildMediaUrl, externalAbsUrl } from '../utils/mediaUrl';
import { TrendingUp, FileText, Mic, Users, Calendar, Hash, ArrowRight, ExternalLink } from 'lucide-react';

interface PaperCardProps {
  paper: Paper;
}

const PaperCard: React.FC<PaperCardProps> = ({ paper }) => {
  const pdfUrl = buildMediaUrl(paper.pdf_url || paper.pdf_path);
  const audioUrl = buildMediaUrl(paper.audio_abstract_url || paper.audio_abstract_path);
  const sourceUrl = paper.source_url || externalAbsUrl(paper.external_id);
  const scoreLabel = formatScore(paper.score);
  const authorsLabel = formatAuthorsShort(paper.authors, 3);
  const dateLabel = formatDate(paper.published);
  const summaryText = truncateText(paper.abstract_vi || paper.abstract_en, 200);

  return (
    <article className="paper-card">
      {/* Header: title + badges */}
      <div className="paper-card__top">
        <div className="paper-card__badges">
          <span className="score-chip"><TrendingUp size={14} className="mr-1" /> {scoreLabel}</span>
          {pdfUrl && <span className="badge badge--pdf"><FileText size={14} className="mr-1" /> PDF</span>}
          {(audioUrl || paper.has_audio) && (
            <span className="badge badge--audio"><Mic size={14} className="mr-1" /> Audio</span>
          )}
        </div>
        <h3 className="paper-card__title">
          <Link to={`/papers/${paper.id}`}>{paper.title}</Link>
        </h3>
      </div>

      {/* Meta row */}
      <div className="paper-card__meta">
        {paper.authors && paper.authors.length > 0 && (
          <span className="meta-tag">
            <Users size={14} className="mr-1" /> {authorsLabel}
          </span>
        )}
        <span className="meta-tag"><Calendar size={14} className="mr-1" /> {dateLabel}</span>
        <span className="meta-tag meta-tag--external"><Hash size={14} className="mr-1" /> {paper.external_id}</span>
      </div>

      {/* Summary / abstract snippet */}
      {summaryText && (
        <p className="paper-card__summary">{summaryText}</p>
      )}

      {/* Actions */}
      <div className="paper-card__actions">
        <Link
          to={`/papers/${paper.id}`}
          className="btn-paper-action btn-paper-action--primary flex items-center justify-center gap-1"
          id={`paper-detail-${paper.id}`}
        >
          View Details <ArrowRight size={16} />
        </Link>
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-paper-action btn-paper-action--arxiv flex items-center justify-center gap-1"
          id={`paper-source-${paper.id}`}
        >
          <ExternalLink size={14} /> Source
        </a>
        {pdfUrl && (
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-paper-action btn-paper-action--pdf flex items-center justify-center gap-1"
            id={`paper-pdf-${paper.id}`}
          >
            <FileText size={14} /> PDF
          </a>
        )}
      </div>
    </article>
  );
};

export default PaperCard;
