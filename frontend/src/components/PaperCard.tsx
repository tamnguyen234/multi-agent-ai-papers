import React from 'react';
import { Link } from 'react-router-dom';
import type { Paper } from '../types/paper';
import { formatAuthorsShort, formatDate, truncateText } from '../utils/formatters';
import { buildMediaUrl, arxivAbsUrl, hfPaperUrl } from '../utils/mediaUrl';

interface PaperCardProps {
  paper: Paper;
}

const PaperCard: React.FC<PaperCardProps> = ({ paper }) => {
  const pdfUrl = buildMediaUrl(paper.pdf_url || paper.pdf_path);
  const audioUrl = buildMediaUrl(paper.audio_abstract_url || paper.audio_abstract_path);
  const arxivUrl = arxivAbsUrl(paper.arxiv_id);
  const hfUrl = hfPaperUrl(paper.arxiv_id);
  const authorsLabel = formatAuthorsShort(paper.authors, 3);
  const dateLabel = formatDate(paper.published);
  const summaryText = truncateText(paper.abstract, 200);

  return (
    <article className="paper-card">
      {/* Header: title + badges */}
      <div className="paper-card__top">
        <div className="paper-card__badges">
          <span className="score-chip">👍 {paper.upvotes}</span>
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
          <span className="meta-tag" title={`${paper.upvotes} upvotes`}>
            👤 {authorsLabel}
          </span>
        )}
        <span className="meta-tag">📅 {dateLabel}</span>
        <span className="meta-tag meta-tag--arxiv">📑 {paper.arxiv_id}</span>
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
          href={hfUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-paper-action btn-paper-action--hf"
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
          id={`paper-hf-${paper.id}`}
        >
          🤗 HuggingFace
        </a>
        <a
          href={arxivUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-paper-action btn-paper-action--arxiv"
          id={`paper-arxiv-${paper.id}`}
        >
          🔗 arXiv
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
