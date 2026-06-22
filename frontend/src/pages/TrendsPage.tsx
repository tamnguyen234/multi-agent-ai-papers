import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ForceGraph2D from 'react-force-graph-2d';
import {
  TrendingUp,
  Network,
  FileText,
  ChevronDown,
  ZoomIn,
  ZoomOut,
  Maximize,
  Minimize,
  Crosshair,
  Brain,
  HelpCircle,
  ExternalLink,
} from 'lucide-react';
import { getTrends, analyzeTrends, getTrendHealth } from '../api/trendApi';
import { normalizeTrendData } from '../utils/trendTransform';
import { getApiErrorMessage } from '../utils/apiError';
import { useToast } from '../context/ToastContext';
import type { TrendPaper } from '../types/trend';
import './TrendsPage.css';

interface ForceNode {
  id: string;
  name: string;
  type: 'topic' | 'keyword';
  size: number;
  group: number;
  topicId: number;
  val: number;
  x?: number;
  y?: number;
  neighbors?: Set<string>;
}

interface ForceLink {
  source: string;
  target: string;
  weight: number;
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  node: ForceNode | null;
}

export const TrendsPage: React.FC = () => {
  const { showToast } = useToast();
  const navigate = useNavigate();
  const graphRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const accordionRef = useRef<HTMLDivElement>(null);
  const topicRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  // API and loading states
  const [trendData, setTrendData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Interactive UI states
  const [expandedTopicId, setExpandedTopicId] = useState<number | null>(null);
  const [hoverNode, setHoverNode] = useState<ForceNode | null>(null);
  const [tooltip, setTooltip] = useState<TooltipState>({ visible: false, x: 0, y: 0, node: null });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showLabels, setShowLabels] = useState(true);
  const [dimensions, setDimensions] = useState({ width: 0, height: 500 });
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Microservice Health
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking');
  const [agentMode, setAgentMode] = useState<string | null>(null);

  // Fetch data
  const fetchTrendsData = useCallback(async (selectFirst = false) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTrends();
      setTrendData(data);
      const normalized = normalizeTrendData(data);
      if (normalized.topics.length > 0 && selectFirst) {
        setExpandedTopicId(normalized.topics[0].id);
      }
    } catch (err: any) {
      console.error('Error fetching trends:', err);
      const msg = getApiErrorMessage(err, 'Không thể kết nối đến máy chủ hoặc chưa cấu hình dữ liệu xu hướng.');
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  // Health check
  const checkAgentHealth = useCallback(async () => {
    setHealthStatus('checking');
    try {
      const res = await getTrendHealth();
      if (res.status === 'ok') {
        setHealthStatus('healthy');
        setAgentMode(res.agent?.mode || 'N/A');
      } else {
        setHealthStatus('unhealthy');
      }
    } catch (err) {
      console.error('Error checking trend agent health:', err);
      setHealthStatus('unhealthy');
      setAgentMode(null);
    }
  }, []);

  useEffect(() => {
    fetchTrendsData(true);
    checkAgentHealth();
  }, []);

  // Safe data normalization
  const normalized = useMemo(() => {
    return normalizeTrendData(trendData);
  }, [trendData]);

  // Adjust graph dimensions
  useEffect(() => {
    if (!containerRef.current) return;

    const updateSize = () => {
      if (!containerRef.current) return;

      setDimensions({
        width: Math.max(containerRef.current.clientWidth, 320),
        height: isFullscreen ? window.innerHeight : 500,
      });
    };

    updateSize();

    const observer = new ResizeObserver(updateSize);
    observer.observe(containerRef.current);

    window.addEventListener('resize', updateSize);

    return () => {
      observer.disconnect();
      window.removeEventListener('resize', updateSize);
    };
  }, [isFullscreen]);

  // Reset graph forces once loaded
  useEffect(() => {
    if (graphRef.current) {
      setTimeout(() => {
        graphRef.current.d3Force('charge')?.strength(-180);
        graphRef.current.zoomToFit(400, 40);
      }, 500);
    }
  }, [trendData]);

  // Re-center and fit graph on dimension changes
  useEffect(() => {
    if (graphRef.current) {
      graphRef.current.d3Force('center')?.x(dimensions.width / 2).y(dimensions.height / 2);
      graphRef.current.d3ReheatSimulation();
      const timer = setTimeout(() => {
        graphRef.current?.zoomToFit(400, 40);
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [dimensions.width, dimensions.height]);

  // Generate D3 network graph nodes & edges
  const forceGraphData = useMemo(() => {
    const nodes: ForceNode[] = [];
    const links: ForceLink[] = [];

    normalized.topics.forEach((topic, idx) => {
      const groupNum = (idx % 6) + 1;
      const topicNodeId = `topic_${topic.id}`;
      const valSize = Math.max(12, Math.min(28, 8 + topic.paper_count * 1.8));

      nodes.push({
        id: topicNodeId,
        name: topic.name,
        type: 'topic',
        size: valSize,
        group: groupNum,
        topicId: topic.id,
        val: valSize,
      });

      const keywords = topic.keywords || [];
      keywords.slice(0, 5).forEach((kw) => {
        const kwNodeId = `keyword_${topic.id}_${kw}`;
        nodes.push({
          id: kwNodeId,
          name: kw,
          type: 'keyword',
          size: 6,
          group: groupNum,
          topicId: topic.id,
          val: 6,
        });
        links.push({ source: kwNodeId, target: topicNodeId, weight: 1.5 });
      });
    });

    // Cross-link topics sharing keywords
    for (let i = 0; i < normalized.topics.length; i++) {
      const topicA = normalized.topics[i];
      const kwsA = new Set((topicA.keywords || []).map((k) => k.toLowerCase()));
      for (let j = i + 1; j < normalized.topics.length; j++) {
        const topicB = normalized.topics[j];
        const kwsB = topicB.keywords || [];
        const hasOverlap = kwsB.some((k) => kwsA.has(k.toLowerCase()));
        if (hasOverlap) {
          links.push({
            source: `topic_${topicA.id}`,
            target: `topic_${topicB.id}`,
            weight: 0.6,
          });
        }
      }
    }

    // Neighbor pointers for hover highlighting
    links.forEach((link: any) => {
      const srcId = typeof link.source === 'object' ? link.source.id : link.source;
      const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
      const a = nodes.find((n) => n.id === srcId);
      const b = nodes.find((n) => n.id === tgtId);
      if (a && b) {
        if (!a.neighbors) a.neighbors = new Set();
        if (!b.neighbors) b.neighbors = new Set();
        a.neighbors.add(b.id);
        b.neighbors.add(a.id);
      }
    });

    return { nodes, links };
  }, [normalized.topics]);

  const getColorByGroup = (group: number) => {
    const colors: Record<number, string> = {
      1: '#10b981',
      2: '#06b6d4',
      3: '#f59e0b',
      4: '#ec4899',
      5: '#6366f1',
      6: '#a855f7',
    };
    return colors[group] || '#94a3b8';
  };

  // Scroll to accordion topic
  const scrollToTopic = useCallback((topicId: number) => {
    setExpandedTopicId(topicId);
    // Small delay so state updates first
    setTimeout(() => {
      const el = topicRefs.current.get(topicId);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else if (accordionRef.current) {
        accordionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 80);
  }, []);

  // Node click → scroll to accordion topic
  const handleNodeClick = useCallback(
    (node: any) => {
      scrollToTopic(node.topicId);
    },
    [scrollToTopic]
  );

  // Node hover → floating tooltip
  const handleNodeHover = useCallback((node: any) => {
    setHoverNode(node || null);
    if (node && containerRef.current) {
      setTooltip((prev) => ({ ...prev, visible: true, node: node }));
    } else {
      setTooltip((prev) => ({ ...prev, visible: false, node: null }));
    }
  }, []);

  // Track mouse position for tooltip
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (tooltip.visible) {
      const rect = containerRef.current?.getBoundingClientRect();
      if (rect) {
        setTooltip((prev) => ({
          ...prev,
          x: e.clientX - rect.left + 16,
          y: e.clientY - rect.top + 16,
        }));
      }
    }
  }, [tooltip.visible]);

  // Toolbar actions
  const handleZoomIn = () => graphRef.current?.zoom(graphRef.current.zoom() * 1.4, 300);
  const handleZoomOut = () => graphRef.current?.zoom(graphRef.current.zoom() / 1.4, 300);
  const handleFit = () => graphRef.current?.zoomToFit(400, 40);

  // Run pipeline analysis
  const handleAnalyze = async () => {
    if (isAnalyzing) return;
    setIsAnalyzing(true);
    showToast('Đang bắt đầu phân tích xu hướng chủ đề khoa học...', 'info');
    try {
      await analyzeTrends();
      showToast('Phân tích xu hướng thành công! Đang cập nhật dữ liệu...', 'success');
      await fetchTrendsData(true);
      await checkAgentHealth();
    } catch (err: any) {
      console.error('Analysis failed:', err);
      const msg = getApiErrorMessage(
        err,
        'Quá trình phân tích xu hướng thất bại. Hãy chắc chắn rằng bạn có đủ bài báo và Trend Agent đang hoạt động.'
      );
      showToast(msg, 'error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Get tooltip content for a node
  const getTooltipContent = (node: ForceNode) => {
    if (node.type === 'topic') {
      const topic = normalized.topics.find((t) => t.id === node.topicId);
      return topic
        ? {
          title: topic.name,
          badge: 'CHỦ ĐỀ',
          lines: [
            `${topic.paper_count} bài báo`,
            topic.confidence_avg > 0
              ? `Độ tin cậy: ${Math.round(topic.confidence_avg * 100)}%`
              : null,
            topic.keywords?.length
              ? `Keywords: ${topic.keywords.slice(0, 3).join(', ')}`
              : null,
          ].filter(Boolean) as string[],
        }
        : null;
    } else {
      const topic = normalized.topics.find((t) => t.id === node.topicId);
      return {
        title: node.name,
        badge: 'TỪ KHÓA',
        lines: topic ? [`Thuộc chủ đề: ${topic.name}`] : [],
      };
    }
  };

  if (loading && !trendData) {
    return (
      <div className="trends-page">
        <div className="trends-loading-container">
          <div className="spinner" />
          <div className="trends-loading-text">Đang tải và đồng bộ dữ liệu xu hướng khoa học AI...</div>
        </div>
      </div>
    );
  }

  if (error && (!trendData || normalized.topics.length === 0)) {
    return (
      <div className="trends-page">
        <div className="trends-error-container">
          <div className="trends-error-text">⚠️ {error}</div>
          <button
            className="trends-retry-btn"
            onClick={() => {
              fetchTrendsData(true);
              checkAgentHealth();
            }}
          >
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="trends-page">
      {/* ── Top Header ── */}
      <div className="trends-header">
        <div className="trends-title-section">
          <h1 className="trends-title">📈 Phân Tích Xu Hướng Chủ Đề</h1>
          <div className="trends-status-container">
            {healthStatus === 'healthy' ? (
              <span className="status-badge status-badge--healthy" title={`Chế độ phân tích: ${agentMode}`}>
                ● Trend Agent: Hoạt động ({agentMode})
              </span>
            ) : healthStatus === 'unhealthy' ? (
              <span className="status-badge status-badge--unhealthy">● Trend Agent: Ngoại tuyến</span>
            ) : (
              <span className="status-badge status-badge--checking">● Trend Agent: Đang kiểm tra...</span>
            )}
          </div>
        </div>

        <button
          className="btn-analyze"
          onClick={handleAnalyze}
          disabled={isAnalyzing || loading}
          id="btn-analyze-trends"
        >
          {isAnalyzing ? (
            <>
              <span className="spinner-small" />
              Đang phân tích...
            </>
          ) : (
            '⚡ Phân tích xu hướng'
          )}
        </button>
      </div>

      {/* ── Summary Cards ── */}
      <div className="trends-summary-grid">
        <div className="trend-summary-card">
          <span className="summary-icon">🏷️</span>
          <div className="summary-info">
            <span className="summary-value">{normalized.topic_count}</span>
            <span className="summary-label">Chủ đề khoa học</span>
          </div>
        </div>
        <div className="trend-summary-card">
          <span className="summary-icon">📄</span>
          <div className="summary-info">
            <span className="summary-value">{normalized.total_papers}</span>
            <span className="summary-label">Bài báo được phân cụm</span>
          </div>
        </div>
        {normalized.topTopic && (
          <div className="trend-summary-card">
            <span className="summary-icon">🔥</span>
            <div className="summary-info">
              <span className="summary-value" title={normalized.topTopic.name}>
                {normalized.topTopic.name}
              </span>
              <span className="summary-label">Chủ đề nổi bật nhất ({normalized.topTopic.paper_count} bài)</span>
            </div>
          </div>
        )}
      </div>

      {normalized.topics.length === 0 ? (
        <div className="trends-error-container">
          <div className="trends-error-text">Chưa có dữ liệu xu hướng khoa học.</div>
          <p style={{ color: 'var(--text-trends-secondary)', fontSize: '0.9rem', marginBottom: '16px' }}>
            Hệ thống cần phân tích các bài báo hiện có để tạo ra các cụm chủ đề khoa học AI nổi bật.
          </p>
          <button className="btn-analyze" onClick={handleAnalyze} disabled={isAnalyzing}>
            Bắt đầu phân tích
          </button>
        </div>
      ) : (
        <>
          {/* ── Section 1: Knowledge Graph (full-width, top) ── */}
          <section className="trends-graph-section">
            <div className={`glass-card graph-card-new ${isFullscreen ? 'graph-card-fullscreen' : ''}`}>
              <div className="card-header">
                <span className="card-header-icon">
                  <Network size={20} />
                </span>
                <h2 className="card-title">Knowledge Graph Discovery</h2>
                <span className="card-header-hint">
                  <HelpCircle size={13} /> Hover để xem thông tin · Click node để mở accordion
                </span>
              </div>

              {/* Graph canvas area */}
              <div className="graph-container" onMouseMove={handleMouseMove} ref={containerRef}>
                {/* Controls toolbar */}
                <div className="graph-toolbar">
                  <button className="toolbar-btn" onClick={handleZoomIn} title="Phóng to">
                    <ZoomIn size={18} />
                  </button>
                  <button className="toolbar-btn" onClick={handleZoomOut} title="Thu nhỏ">
                    <ZoomOut size={18} />
                  </button>
                  <button className="toolbar-btn" onClick={handleFit} title="Căn giữa biểu đồ">
                    <Crosshair size={18} />
                  </button>
                  <div className="toolbar-divider" />
                  <button
                    className="toolbar-btn"
                    onClick={() => setShowLabels(!showLabels)}
                    title={showLabels ? 'Ẩn nhãn chữ' : 'Hiện nhãn chữ'}
                    style={{ color: showLabels ? '#60a5fa' : 'var(--text-trends-primary)' }}
                  >
                    <Brain size={18} />
                  </button>
                  <button
                    className="toolbar-btn"
                    onClick={() => setIsFullscreen(!isFullscreen)}
                    title={isFullscreen ? 'Thoát toàn màn hình' : 'Toàn màn hình'}
                  >
                    {isFullscreen ? <Minimize size={18} /> : <Maximize size={18} />}
                  </button>
                </div>

                {/* D3 force graph */}
                {forceGraphData.nodes.length > 0 && (
                  <ForceGraph2D
                    ref={graphRef}
                    graphData={forceGraphData}
                    width={dimensions.width}
                    height={dimensions.height}
                    backgroundColor="#0b0f19"
                    nodeRelSize={1}
                    onNodeHover={handleNodeHover}
                    onNodeClick={handleNodeClick}
                    linkColor={(link: any) => {
                      if (!hoverNode) return 'rgba(255,255,255,0.06)';
                      const srcId = typeof link.source === 'object' ? link.source.id : link.source;
                      const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
                      const isLinkHovered = srcId === hoverNode.id || tgtId === hoverNode.id;
                      return isLinkHovered
                        ? getColorByGroup(hoverNode.group)
                        : 'rgba(255,255,255,0.01)';
                    }}
                    linkWidth={(link: any) => {
                      if (!hoverNode) return link.weight * 1.5;
                      const srcId = typeof link.source === 'object' ? link.source.id : link.source;
                      const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
                      const isLinkHovered = srcId === hoverNode.id || tgtId === hoverNode.id;
                      return isLinkHovered ? link.weight * 3 : link.weight * 0.5;
                    }}
                    nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D, globalScale: number) => {
                      if (!showLabels) {
                        ctx.fillStyle = color;
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, node.size / globalScale, 0, 2 * Math.PI);
                        ctx.fill();
                        return;
                      }
                      const label = node.name;
                      const baseSize = node.type === 'topic' ? 12 : 8;
                      const fontSize = baseSize / globalScale;
                      ctx.font = `600 ${fontSize}px Inter, sans-serif`;
                      const textWidth = ctx.measureText(label).width;
                      const bckgDimensions = [textWidth, fontSize].map((n) => n + fontSize * 0.5);
                      ctx.fillStyle = color;
                      ctx.fillRect(
                        node.x - bckgDimensions[0] / 2,
                        node.y - bckgDimensions[1] / 2,
                        bckgDimensions[0],
                        bckgDimensions[1]
                      );
                    }}
                    nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
                      const label = node.name;
                      const isHovered = hoverNode && hoverNode.id === node.id;
                      const isNeighbor = hoverNode && hoverNode.neighbors && hoverNode.neighbors.has(node.id);
                      const isFaded = hoverNode && !isHovered && !isNeighbor;

                      const baseSize = node.type === 'topic' ? 12 : 7;
                      const scaleSize = isHovered ? baseSize * 1.3 : baseSize;
                      const fontSize = scaleSize / globalScale;

                      ctx.globalAlpha = isFaded ? 0.2 : 1.0;
                      const nodeColor = getColorByGroup(node.group);

                      if (!isFaded) {
                        ctx.shadowColor = nodeColor;
                        ctx.shadowBlur = isHovered ? 12 : 6;
                      }

                      if (!showLabels) {
                        ctx.fillStyle = nodeColor;
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, node.type === 'topic' ? 8 : 4, 0, 2 * Math.PI);
                        ctx.fill();
                      } else {
                        ctx.font = `${node.type === 'topic' ? '700' : '400'} ${fontSize}px Inter, sans-serif`;
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillStyle = isHovered
                          ? '#ffffff'
                          : node.type === 'topic'
                            ? nodeColor
                            : '#b3bac4';
                        ctx.fillText(label, node.x, node.y);

                        if (node.type === 'keyword') {
                          ctx.fillStyle = nodeColor;
                          ctx.beginPath();
                          ctx.arc(node.x, node.y - fontSize * 0.8, 2 / globalScale, 0, 2 * Math.PI);
                          ctx.fill();
                        }
                      }

                      ctx.shadowBlur = 0;
                      ctx.globalAlpha = 1.0;
                    }}
                  />
                )}

                {/* Floating tooltip */}
                {tooltip.visible && tooltip.node && (
                  <div
                    className="tooltip-card"
                    style={{ left: tooltip.x, top: tooltip.y }}
                    aria-hidden="true"
                  >
                    {(() => {
                      const content = getTooltipContent(tooltip.node);
                      if (!content) return null;
                      const color = getColorByGroup(tooltip.node.group);
                      return (
                        <>
                          <div className="tooltip-card__badge" style={{ color, borderColor: color + '44', backgroundColor: color + '18' }}>
                            {content.badge}
                          </div>
                          <div className="tooltip-card__title">{content.title}</div>
                          {content.lines.map((line, i) => (
                            <div key={i} className="tooltip-card__line">{line}</div>
                          ))}
                          {tooltip.node.type === 'topic' && (
                            <div className="tooltip-card__hint">↓ Click để xem bài báo</div>
                          )}
                        </>
                      );
                    })()}
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* ── Section 2: Topic Accordion (full-width, below) ── */}
          <section className="trends-accordion-section" ref={accordionRef}>
            <div className="glass-card accordion-card">
              <div className="card-header">
                <span className="card-header-icon">
                  <TrendingUp size={20} />
                </span>
                <h2 className="card-title">Trend Topic Leaderboard</h2>
                <span className="accordion-topic-count">{normalized.topics.length} chủ đề</span>
              </div>

              <div className="accordion-list">
                {normalized.topics.map((topic, idx) => {
                  const isExpanded = expandedTopicId === topic.id;
                  const groupNum = (idx % 6) + 1;
                  const color = getColorByGroup(groupNum);

                  return (
                    <div
                      key={topic.id}
                      className={`accordion-item ${isExpanded ? 'accordion-item--expanded' : ''}`}
                      ref={(el) => {
                        if (el) topicRefs.current.set(topic.id, el);
                        else topicRefs.current.delete(topic.id);
                      }}
                    >
                      {/* Accordion header */}
                      <button
                        className="accordion-header"
                        onClick={() => setExpandedTopicId(isExpanded ? null : topic.id)}
                        aria-expanded={isExpanded}
                      >
                        {/* Rank badge */}
                        <span className="accordion-rank" style={{ backgroundColor: color + '22', color }}>
                          #{idx + 1}
                        </span>

                        <div className="accordion-header__info">
                          <span className="accordion-topic-name" style={{ color }}>
                            {topic.name}
                          </span>
                          <div className="accordion-meta">
                            <span className="meta-item">
                              <FileText size={12} /> {topic.paper_count} bài báo
                            </span>
                            {topic.confidence_avg > 0 && (
                              <span className="meta-item">
                                Độ tin cậy:{' '}
                                <span className="confidence-badge">{Math.round(topic.confidence_avg * 100)}%</span>
                              </span>
                            )}
                            {topic.keywords && topic.keywords.length > 0 && (
                              <span className="meta-item meta-item--keywords">
                                {topic.keywords.slice(0, 3).map((kw, ki) => (
                                  <span key={ki} className="keyword-pill" style={{ color, borderColor: color + '44' }}>
                                    #{kw}
                                  </span>
                                ))}
                              </span>
                            )}
                          </div>
                        </div>

                        <span className="accordion-chevron" style={{ transform: isExpanded ? 'rotate(180deg)' : 'none' }}>
                          <ChevronDown size={18} />
                        </span>
                      </button>

                      {/* Accordion body — paper cards */}
                      {isExpanded && (
                        <div className="accordion-body">
                          {topic.description && (
                            <p className="accordion-description">{topic.description}</p>
                          )}

                          {/* All keywords */}
                          {topic.keywords && topic.keywords.length > 0 && (
                            <div className="accordion-keywords-row">
                              {topic.keywords.map((kw, ki) => (
                                <span key={ki} className="keyword-chip" style={{ color, borderColor: color + '44' }}>
                                  #{kw}
                                </span>
                              ))}
                            </div>
                          )}

                          <div className="accordion-papers-label">
                            <FileText size={14} /> Bài báo trong cụm ({topic.papers?.length ?? 0})
                          </div>

                          <div className="accordion-papers-grid">
                            {(topic.papers || []).map((paper: TrendPaper, pIdx: number) => (
                              <div
                                key={paper.id || pIdx}
                                className="accordion-paper-card"
                                onClick={() => navigate(`/papers/${paper.id}`)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' || e.key === ' ') navigate(`/papers/${paper.id}`);
                                }}
                                title={`Xem chi tiết: ${paper.title}`}
                              >
                                <div className="accordion-paper-card__body">
                                  <h4 className="accordion-paper-title">{paper.title}</h4>
                                  {paper.abstract_en && (
                                    <p className="accordion-paper-abstract">{paper.abstract_en}</p>
                                  )}
                                </div>
                                <div className="accordion-paper-card__footer">
                                  {paper.published && (
                                    <span className="accordion-paper-date">
                                      {new Date(paper.published).toLocaleDateString('vi-VN')}
                                    </span>
                                  )}
                                  <span className="accordion-paper-link" style={{ color }}>
                                    <ExternalLink size={13} /> Xem chi tiết
                                  </span>
                                </div>
                              </div>
                            ))}
                            {(!topic.papers || topic.papers.length === 0) && (
                              <p className="accordion-no-papers">Không có bài báo nào trong cụm này.</p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default TrendsPage;
