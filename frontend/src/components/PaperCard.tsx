import React from 'react';
import { Link } from 'react-router-dom';
import type { Paper } from '../types/paper';
import { formatAuthorsShort, formatDate, formatScore, truncateText } from '../utils/formatters';
import { buildMediaUrl, externalAbsUrl } from '../utils/mediaUrl';

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
          <span className="score-chip">⭐ {scoreLabel}</span>
          {pdfUrl && <span className="badge badge--pdf">📄 PDF</span>}
          {(audioUrl || paper.has_audio) && (
            <span className="badge badge--audio">🎙️ Audio</span>
          )}
        </div>
        <h3 className="paper-card__title">
          <Link to={`/papers/${paper.id}`}>{paper.title}</Link>
        </h3>
      </div>

      {/* Meta row */}
      <div className="paper-card__meta">
        {paper.authors && paper.authors.length > 0 && (
          <span className="meta-tag" title={formatScore(paper.score)}>
            👤 {authorsLabel}
          </span>
        )}
        <span className="meta-tag">📅 {dateLabel}</span>
        <span className="meta-tag meta-tag--external">📑 {paper.external_id}</span>
      </div>

      {/* Summary / abstract snippet */}
      {summaryText && (
        <p className="paper-card__summary">{summaryText}</p>
      )}

      {/* Actions */}
      <div className="paper-card__actions">
        <Link
          to={`/papers/${paper.id}`}
          className="btn-paper-action btn-paper-action--primary"
          id={`paper-detail-${paper.id}`}
        >
          Xem chi tiết →
        </Link>
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-paper-action btn-paper-action--arxiv"
          id={`paper-source-${paper.id}`}
        >
          🔗 Nguồn
        </a>
        {pdfUrl && (
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-paper-action btn-paper-action--pdf"
            id={`paper-pdf-${paper.id}`}
          >
            📄 PDF
          </a>
        )}
      </div>
    </article>
  );
};

export default PaperCard;
