import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { getPapers } from '../api/paperApi';
import { getApiErrorMessage } from '../utils/apiError';
import type { Paper } from '../types/paper';
import PaperCard from '../components/PaperCard';
import { buildMediaUrl } from '../utils/mediaUrl';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import EmptyState from '../components/ui/EmptyState';

type SortKey = 'published' | 'score' | 'title';
type FilterAudio = 'all' | 'has_audio' | 'no_audio';
type FilterPdf = 'all' | 'has_pdf' | 'no_pdf';

export const PapersPage: React.FC = () => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Controls
  const [searchText, setSearchText] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('published');
  const [filterAudio, setFilterAudio] = useState<FilterAudio>('all');
  const [filterPdf, setFilterPdf] = useState<FilterPdf>('all');

  const fetchPapers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPapers({ limit: 100 });
      setPapers(data);
    } catch (err: unknown) {
      const msg = getApiErrorMessage(err, 'Không thể tải danh sách bài báo.');
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPapers();
  }, [fetchPapers]);

  // Client-side filter + sort
  const displayed = useMemo(() => {
    let result = [...papers];

    // Search: title, arxiv_id, authors
    if (searchText.trim()) {
      const q = searchText.trim().toLowerCase();
      result = result.filter((p) => {
        const authorsStr = Array.isArray(p.authors) ? p.authors.join(' ') : (p.authors ?? '');
        return (
          p.title.toLowerCase().includes(q) ||
          p.arxiv_id.toLowerCase().includes(q) ||
          authorsStr.toLowerCase().includes(q)
        );
      });
    }

    // Filter audio
    if (filterAudio === 'has_audio') {
      result = result.filter(
        (p) => p.has_audio || !!buildMediaUrl(p.audio_abstract_url || p.audio_abstract_path)
      );
    } else if (filterAudio === 'no_audio') {
      result = result.filter(
        (p) => !p.has_audio && !buildMediaUrl(p.audio_abstract_url || p.audio_abstract_path)
      );
    }

    // Filter PDF
    if (filterPdf === 'has_pdf') {
      result = result.filter((p) => !!buildMediaUrl(p.pdf_url || p.pdf_path));
    } else if (filterPdf === 'no_pdf') {
      result = result.filter((p) => !buildMediaUrl(p.pdf_url || p.pdf_path));
    }

    // Sort
    result.sort((a, b) => {
      if (sortKey === 'published') {
        const da = a.published ?? a.created_at ?? '';
        const db = b.published ?? b.created_at ?? '';
        return db.localeCompare(da);
      }
      if (sortKey === 'score') {
        return b.score - a.score;
      }
      // title A-Z
      return a.title.localeCompare(b.title, 'vi');
    });

    return result;
  }, [papers, searchText, sortKey, filterAudio, filterPdf]);

  const handleClearFilters = () => {
    setSearchText('');
    setSortKey('published');
    setFilterAudio('all');
    setFilterPdf('all');
  };

  const hasActiveFilters =
    searchText.trim() !== '' ||
    sortKey !== 'published' ||
    filterAudio !== 'all' ||
    filterPdf !== 'all';

  return (
    <div className="papers-page">
      {/* Page header */}
      <div className="papers-page__header">
        <div>
          <h1 className="papers-page__title">📄 Danh sách Bài báo</h1>
          <p className="papers-page__subtitle">
            {loading
              ? 'Đang tải…'
              : `${displayed.length} / ${papers.length} bài báo`}
          </p>
        </div>
        <button
          className="btn-refresh"
          onClick={fetchPapers}
          disabled={loading}
          id="btn-refresh-papers"
        >
          {loading ? <span className="spinner-small" /> : '↺ Làm mới'}
        </button>
      </div>

      {/* Toolbar */}
      <div className="papers-toolbar">
        {/* Search */}
        <div className="toolbar-search">
          <span className="toolbar-search__icon">🔍</span>
          <input
            id="papers-search"
            type="text"
            className="toolbar-search__input"
            placeholder="Tìm theo tiêu đề, ID bài báo, tác giả…"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
          {searchText && (
            <button
              className="toolbar-search__clear"
              onClick={() => setSearchText('')}
              aria-label="Xóa tìm kiếm"
            >
              ×
            </button>
          )}
        </div>

        {/* Sort */}
        <div className="toolbar-control">
          <label htmlFor="papers-sort" className="toolbar-label">Sắp xếp:</label>
          <select
            id="papers-sort"
            className="toolbar-select"
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value as SortKey)}
          >
            <option value="published">Mới nhất</option>
            <option value="score">Điểm cao nhất</option>
            <option value="title">Tiêu đề A-Z</option>
          </select>
        </div>

        {/* Filter Audio */}
        <div className="toolbar-control">
          <label htmlFor="papers-filter-audio" className="toolbar-label">Audio:</label>
          <select
            id="papers-filter-audio"
            className="toolbar-select"
            value={filterAudio}
            onChange={(e) => setFilterAudio(e.target.value as FilterAudio)}
          >
            <option value="all">Tất cả</option>
            <option value="has_audio">Có audio</option>
            <option value="no_audio">Chưa có audio</option>
          </select>
        </div>

        {/* Filter PDF */}
        <div className="toolbar-control">
          <label htmlFor="papers-filter-pdf" className="toolbar-label">PDF:</label>
          <select
            id="papers-filter-pdf"
            className="toolbar-select"
            value={filterPdf}
            onChange={(e) => setFilterPdf(e.target.value as FilterPdf)}
          >
            <option value="all">Tất cả</option>
            <option value="has_pdf">Có PDF</option>
            <option value="no_pdf">Chưa có PDF</option>
          </select>
        </div>

        {/* Clear */}
        {hasActiveFilters && (
          <button className="btn-clear-filters" onClick={handleClearFilters}>
            ✕ Xóa bộ lọc
          </button>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <LoadingState message="Đang tải danh sách bài báo…" />
      )}

      {/* Error */}
      {!loading && error && (
        <ErrorState message={error} onRetry={fetchPapers} />
      )}

      {/* Empty */}
      {!loading && !error && displayed.length === 0 && (
        <EmptyState
          title={papers.length === 0 ? 'Chưa có bài báo nào' : 'Không tìm thấy kết quả phù hợp'}
          message={papers.length === 0
            ? 'Hãy chạy Daily Digest Job từ Dashboard để lấy bài báo mới từ HuggingFace.'
            : 'Thử thay đổi từ khóa hoặc bộ lọc của bạn.'}
          icon={papers.length === 0 ? '📭' : '🔎'}
          actionLabel={hasActiveFilters ? 'Xóa bộ lọc' : undefined}
          onAction={hasActiveFilters ? handleClearFilters : undefined}
        />
      )}

      {/* Paper cards grid */}
      {!loading && !error && displayed.length > 0 && (
        <div className="papers-grid">
          {displayed.map((paper) => (
            <PaperCard key={paper.id} paper={paper} />
          ))}
        </div>
      )}
    </div>
  );
};
