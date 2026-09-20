import React, { useState } from 'react';

/**
 * Clean SVG Donut Chart for Sentiment Breakdown with Center Health Metric
 */
export function SentimentDonutChart({ positive = 0, neutral = 0, negative = 0, healthScore = null }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  const total = (positive || 0) + (neutral || 0) + (negative || 0);
  const data = [
    { label: 'Positive', count: positive, color: '#10B981', bg: 'rgba(16, 185, 129, 0.12)' },
    { label: 'Neutral', count: neutral, color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.12)' },
    { label: 'Negative', count: negative, color: '#EF4444', bg: 'rgba(239, 68, 68, 0.12)' },
  ];

  if (total === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
        No sentiment data available
      </div>
    );
  }

  // Calculate SVG arc paths
  const size = 200;
  const strokeWidth = 26;
  const radius = (size - strokeWidth) / 2;
  const center = size / 2;
  const circumference = 2 * Math.PI * radius;

  let accumulatedPercent = 0;
  const slices = data.map((item, idx) => {
    const percent = total > 0 ? item.count / total : 0;
    const strokeDasharray = `${percent * circumference} ${circumference}`;
    const strokeDashoffset = -accumulatedPercent * circumference;
    accumulatedPercent += percent;

    return {
      ...item,
      percent: Math.round(percent * 100),
      strokeDasharray,
      strokeDashoffset,
      idx,
    };
  });

  const activeSlice = hoveredIndex !== null ? slices[hoveredIndex] : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', width: '100%' }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
          {/* Background circle track */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="transparent"
            stroke="var(--border)"
            strokeWidth={strokeWidth}
          />
          {slices.map((slice) => (
            <circle
              key={slice.label}
              cx={center}
              cy={center}
              r={radius}
              fill="transparent"
              stroke={slice.color}
              strokeWidth={hoveredIndex === slice.idx ? strokeWidth + 4 : strokeWidth}
              strokeDasharray={slice.strokeDasharray}
              strokeDashoffset={slice.strokeDashoffset}
              strokeLinecap="round"
              style={{
                transition: 'all 0.25s ease',
                cursor: 'pointer',
                opacity: hoveredIndex === null || hoveredIndex === slice.idx ? 1 : 0.45,
              }}
              onMouseEnter={() => setHoveredIndex(slice.idx)}
              onMouseLeave={() => setHoveredIndex(null)}
            />
          ))}
        </svg>

        {/* Center Content Gauge */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: size,
            height: size,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
          }}
        >
          {activeSlice ? (
            <>
              <span style={{ fontSize: '22px', fontWeight: 700, color: activeSlice.color }}>
                {activeSlice.percent}%
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>
                {activeSlice.label} ({activeSlice.count})
              </span>
            </>
          ) : (
            <>
              <span style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text)' }}>
                {healthScore !== null ? `${healthScore}%` : `${slices[0].percent}%`}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Health Score
              </span>
            </>
          )}
        </div>
      </div>

      {/* Legend Chips */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', flexWrap: 'wrap', width: '100%' }}>
        {slices.map((slice) => (
          <div
            key={slice.label}
            onMouseEnter={() => setHoveredIndex(slice.idx)}
            onMouseLeave={() => setHoveredIndex(null)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '20px',
              backgroundColor: hoveredIndex === slice.idx ? slice.bg : 'var(--bg)',
              border: `1px solid ${hoveredIndex === slice.idx ? slice.color : 'var(--border)'}`,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              fontSize: '12px',
            }}
          >
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: slice.color }}></span>
            <span style={{ fontWeight: 600, color: 'var(--text)' }}>{slice.label}</span>
            <span style={{ color: 'var(--text-muted)' }}>({slice.count} • {slice.percent}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Vibrant, distinct, high-contrast category palette
export const categoryColors = {
  feature_request: '#2563EB',    // Radiant Royal Blue
  bug_report: '#EF4444',         // Vivid Coral / Crimson Red
  performance_issue: '#F59E0B',  // Vivid Amber Gold
  ui_ux: '#8B5CF6',              // Radiant Violet / Purple
  general_feedback: '#10B981',   // Crisp Emerald Green
  customer_support: '#EC4899',   // Vivid Fuchsia / Pink
  integration: '#06B6D4',        // Bright Cyan
  security: '#6366F1',           // Indigo
};

export const defaultCategoryPalette = [
  '#2563EB', // Blue
  '#EF4444', // Red
  '#F59E0B', // Amber
  '#8B5CF6', // Purple
  '#10B981', // Emerald
  '#EC4899', // Pink
  '#06B6D4', // Cyan
  '#6366F1', // Indigo
  '#14B8A6', // Teal
  '#F97316', // Orange
];

export function getCategoryColor(category, idx = 0) {
  if (!category) return defaultCategoryPalette[idx % defaultCategoryPalette.length];
  const normalized = category.toLowerCase().trim().replace(/[\s-]+/g, '_');
  return categoryColors[normalized] || defaultCategoryPalette[idx % defaultCategoryPalette.length];
}

/**
 * Multi-Mode Category Breakdown Visuals:
 * - Donut Chart View
 * - Horizontal Ranked Bars View
 * - Grid Matrix View
 */
export function CategoryPieChart({ categoryDistribution = {}, totalFeedback = 0, onSelectCategory }) {
  const [hoveredCategory, setHoveredCategory] = useState(null);
  const [viewMode, setViewMode] = useState('donut'); // 'donut' | 'bars' | 'grid'

  const entries = Object.entries(categoryDistribution).filter(([_, count]) => count > 0);
  const total = entries.reduce((sum, [_, count]) => sum + count, 0);

  if (total === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
        No category distribution data available
      </div>
    );
  }

  const size = 180;
  const strokeWidth = 24;
  const radius = (size - strokeWidth) / 2;
  const center = size / 2;
  const circumference = 2 * Math.PI * radius;

  let accumulatedPercent = 0;
  const slices = entries.map(([category, count], idx) => {
    const percent = count / total;
    const strokeDasharray = `${percent * circumference} ${circumference}`;
    const strokeDashoffset = -accumulatedPercent * circumference;
    accumulatedPercent += percent;
    const color = getCategoryColor(category, idx);

    return {
      category,
      label: category.replace(/_/g, ' '),
      count,
      percent: Math.round(percent * 100),
      color,
      strokeDasharray,
      strokeDashoffset,
      idx,
    };
  });

  const activeSlice = hoveredCategory !== null ? slices.find((s) => s.category === hoveredCategory) : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', width: '100%' }}>
      {/* View Switcher Tabs */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', background: 'var(--bg)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border)', alignSelf: 'center' }}>
        <button
          onClick={() => setViewMode('donut')}
          style={{
            padding: '4px 12px',
            fontSize: '11px',
            fontWeight: 600,
            borderRadius: '6px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: viewMode === 'donut' ? 'var(--bg-card)' : 'transparent',
            color: viewMode === 'donut' ? 'var(--text)' : 'var(--text-muted)',
            boxShadow: viewMode === 'donut' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            transition: 'all 0.15s ease',
          }}
        >
          Donut Chart
        </button>
        <button
          onClick={() => setViewMode('bars')}
          style={{
            padding: '4px 12px',
            fontSize: '11px',
            fontWeight: 600,
            borderRadius: '6px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: viewMode === 'bars' ? 'var(--bg-card)' : 'transparent',
            color: viewMode === 'bars' ? 'var(--text)' : 'var(--text-muted)',
            boxShadow: viewMode === 'bars' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            transition: 'all 0.15s ease',
          }}
        >
          Ranked Bars
        </button>
        <button
          onClick={() => setViewMode('grid')}
          style={{
            padding: '4px 12px',
            fontSize: '11px',
            fontWeight: 600,
            borderRadius: '6px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: viewMode === 'grid' ? 'var(--bg-card)' : 'transparent',
            color: viewMode === 'grid' ? 'var(--text)' : 'var(--text-muted)',
            boxShadow: viewMode === 'grid' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            transition: 'all 0.15s ease',
          }}
        >
          Matrix Grid
        </button>
      </div>

      {/* MODE 1: DONUT VIEW */}
      {viewMode === 'donut' && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px', width: '100%' }}>
          <div style={{ position: 'relative', width: size, height: size }}>
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
              <circle
                cx={center}
                cy={center}
                r={radius}
                fill="transparent"
                stroke="var(--border)"
                strokeWidth={strokeWidth}
              />
              {slices.map((slice) => (
                <circle
                  key={slice.category}
                  cx={center}
                  cy={center}
                  r={radius}
                  fill="transparent"
                  stroke={slice.color}
                  strokeWidth={hoveredCategory === slice.category ? strokeWidth + 5 : strokeWidth}
                  strokeDasharray={slice.strokeDasharray}
                  strokeDashoffset={slice.strokeDashoffset}
                  strokeLinecap="round"
                  style={{
                    transition: 'all 0.2s ease',
                    cursor: 'pointer',
                    opacity: hoveredCategory === null || hoveredCategory === slice.category ? 1 : 0.4,
                  }}
                  onMouseEnter={() => setHoveredCategory(slice.category)}
                  onMouseLeave={() => setHoveredCategory(null)}
                  onClick={() => onSelectCategory && onSelectCategory(slice.category)}
                />
              ))}
            </svg>

            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: size,
                height: size,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                pointerEvents: 'none',
                padding: '12px',
                textAlign: 'center',
              }}
            >
              {activeSlice ? (
                <>
                  <span style={{ fontSize: '20px', fontWeight: 800, color: activeSlice.color }}>
                    {activeSlice.percent}%
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text)', fontWeight: 600, textTransform: 'capitalize' }}>
                    {activeSlice.label}
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                    ({activeSlice.count} items)
                  </span>
                </>
              ) : (
                <>
                  <span style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text)' }}>
                    {total}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>
                    Total Items
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MODE 2: RANKED BARS VIEW */}
      {viewMode === 'bars' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%', padding: '4px 0' }}>
          {slices.map((slice) => (
            <div
              key={slice.category}
              onMouseEnter={() => setHoveredCategory(slice.category)}
              onMouseLeave={() => setHoveredCategory(null)}
              onClick={() => onSelectCategory && onSelectCategory(slice.category)}
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                backgroundColor: hoveredCategory === slice.category ? `${slice.color}10` : 'var(--bg)',
                border: `1px solid ${hoveredCategory === slice.category ? slice.color : 'var(--border)'}`,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', fontSize: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: slice.color }}></span>
                  <strong style={{ color: 'var(--text)', textTransform: 'capitalize' }}>{slice.label}</strong>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 700, color: slice.color }}>{slice.percent}%</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>({slice.count} items)</span>
                </div>
              </div>
              <div style={{ height: '7px', borderRadius: '4px', backgroundColor: 'var(--border)', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${slice.percent}%`,
                    height: '100%',
                    backgroundColor: slice.color,
                    borderRadius: '4px',
                    transition: 'width 0.4s ease',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* MODE 3: MATRIX GRID VIEW */}
      {viewMode === 'grid' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px', width: '100%' }}>
          {slices.map((slice) => (
            <div
              key={slice.category}
              onMouseEnter={() => setHoveredCategory(slice.category)}
              onMouseLeave={() => setHoveredCategory(null)}
              onClick={() => onSelectCategory && onSelectCategory(slice.category)}
              style={{
                padding: '12px 10px',
                borderRadius: '8px',
                backgroundColor: hoveredCategory === slice.category ? `${slice.color}15` : 'var(--bg)',
                border: `1px solid ${hoveredCategory === slice.category ? slice.color : 'var(--border)'}`,
                borderTop: `3px solid ${slice.color}`,
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'capitalize', marginBottom: '4px' }}>
                {slice.label}
              </div>
              <div style={{ fontSize: '20px', fontWeight: 800, color: slice.color }}>
                {slice.count}
              </div>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text)', marginTop: '2px' }}>
                {slice.percent}% share
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Interactive Multi-Series Trend Area Chart
 */
export function TrendAreaChart({ trends = [] }) {
  const [hoveredPoint, setHoveredPoint] = useState(null);

  if (!trends || trends.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
        No trend records available to visualize yet.
      </div>
    );
  }

  const width = 760;
  const height = 240;
  const padding = { top: 20, right: 30, bottom: 40, left: 40 };

  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Max volume for scaling Y
  const maxVolume = Math.max(...trends.map((t) => t.total_count || 0), 5);

  const getX = (index) => {
    if (trends.length <= 1) return padding.left + chartWidth / 2;
    return padding.left + (index / (trends.length - 1)) * chartWidth;
  };

  const getY = (val) => {
    return padding.top + chartHeight - (val / maxVolume) * chartHeight;
  };

  // Build SVG path strings
  const buildAreaPath = (key) => {
    if (trends.length === 0) return '';
    const points = trends.map((t, idx) => `${getX(idx)},${getY(t[key] || 0)}`);
    const firstX = getX(0);
    const lastX = getX(trends.length - 1);
    const bottomY = padding.top + chartHeight;
    return `M ${firstX},${bottomY} L ${points.join(' L ')} L ${lastX},${bottomY} Z`;
  };

  const buildLinePath = (key) => {
    if (trends.length === 0) return '';
    const points = trends.map((t, idx) => `${getX(idx)},${getY(t[key] || 0)}`);
    return `M ${points.join(' L ')}`;
  };

  const totalArea = buildAreaPath('total_count');
  const totalLine = buildLinePath('total_count');
  const posLine = buildLinePath('positive_count');
  const negLine = buildLinePath('negative_count');

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <div style={{ minWidth: '600px', position: 'relative' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          <defs>
            <linearGradient id="totalGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#355C52" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#355C52" stopOpacity="0.02" />
            </linearGradient>
            <linearGradient id="posGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2E7D32" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#2E7D32" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = padding.top + chartHeight * (1 - pct);
            const val = Math.round(maxVolume * pct);
            return (
              <g key={idx}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="var(--border)"
                  strokeDasharray="4 4"
                  strokeWidth="1"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="11"
                  fill="var(--text-muted)"
                >
                  {val}
                </text>
              </g>
            );
          })}

          {/* Area under Total Volume */}
          <path d={totalArea} fill="url(#totalGrad)" />

          {/* Lines */}
          <path d={totalLine} fill="none" stroke="#355C52" strokeWidth="2.5" />
          <path d={posLine} fill="none" stroke="#2E7D32" strokeWidth="2" strokeDasharray="5 3" />
          <path d={negLine} fill="none" stroke="#C62828" strokeWidth="2" strokeDasharray="5 3" />

          {/* Data Points */}
          {trends.map((t, idx) => {
            const x = getX(idx);
            const y = getY(t.total_count);
            const isHovered = hoveredPoint?.period === t.period;

            return (
              <g key={t.period}>
                {/* Invisible hover trigger column */}
                <rect
                  x={x - 15}
                  y={padding.top}
                  width="30"
                  height={chartHeight}
                  fill="transparent"
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHoveredPoint(t)}
                  onMouseLeave={() => setHoveredPoint(null)}
                />

                {/* Vertical hover guide */}
                {isHovered && (
                  <line
                    x1={x}
                    y1={padding.top}
                    x2={x}
                    y2={padding.top + chartHeight}
                    stroke="#355C52"
                    strokeWidth="1.5"
                    strokeDasharray="3 3"
                  />
                )}

                {/* Point circle */}
                <circle
                  cx={x}
                  cy={y}
                  r={isHovered ? 6 : 4}
                  fill={isHovered ? '#203C35' : '#355C52'}
                  stroke="#FFFFFF"
                  strokeWidth="2"
                  style={{ transition: 'all 0.15s ease' }}
                />

                {/* X-axis date labels (render every 2nd or 3rd if many points) */}
                {(trends.length <= 8 || idx % Math.ceil(trends.length / 7) === 0 || idx === trends.length - 1) && (
                  <text
                    x={x}
                    y={height - padding.bottom + 20}
                    textAnchor="middle"
                    fontSize="11"
                    fill="var(--text-muted)"
                  >
                    {t.period.length > 5 ? t.period.slice(5) : t.period}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip Overlay */}
        {hoveredPoint && (
          <div
            style={{
              position: 'absolute',
              top: '10px',
              right: '20px',
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '10px 14px',
              boxShadow: 'var(--shadow-md)',
              fontSize: '12px',
              zIndex: 10,
              pointerEvents: 'none',
              minWidth: '180px',
            }}
          >
            <div style={{ fontWeight: 700, color: 'var(--text)', marginBottom: '4px' }}>
              {hoveredPoint.period}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', margin: '2px 0' }}>
              <span style={{ color: '#355C52', fontWeight: 600 }}>Total Volume:</span>
              <strong>{hoveredPoint.total_count}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', margin: '2px 0' }}>
              <span style={{ color: '#2E7D32' }}>Positive:</span>
              <span>{hoveredPoint.positive_count}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', margin: '2px 0' }}>
              <span style={{ color: '#E65100' }}>Neutral:</span>
              <span>{hoveredPoint.neutral_count}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', margin: '2px 0' }}>
              <span style={{ color: '#C62828' }}>Negative:</span>
              <span>{hoveredPoint.negative_count}</span>
            </div>
            {hoveredPoint.top_category && (
              <div style={{ marginTop: '6px', paddingTop: '4px', borderTop: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                Top: <strong>{hoveredPoint.top_category.replace(/_/g, ' ')}</strong>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Graph Legend */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginTop: '10px', fontSize: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '16px', height: '3px', backgroundColor: '#355C52', display: 'inline-block' }}></span>
          <span style={{ color: 'var(--text)', fontWeight: 600 }}>Total Feedback Volume</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '16px', height: '2px', backgroundColor: '#2E7D32', borderTop: '1px dashed #2E7D32', display: 'inline-block' }}></span>
          <span style={{ color: 'var(--text-muted)' }}>Positive Trajectory</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '16px', height: '2px', backgroundColor: '#C62828', borderTop: '1px dashed #C62828', display: 'inline-block' }}></span>
          <span style={{ color: 'var(--text-muted)' }}>Negative Trajectory</span>
        </div>
      </div>
    </div>
  );
}

/**
 * Severity Distribution Gauge / Bar for Customer Pain Points
 */
export function SeverityBarChart({ painPoints = [] }) {
  const total = painPoints.length;
  if (total === 0) return null;

  const high = painPoints.filter((p) => p.severity === 'high').length;
  const med = painPoints.filter((p) => p.severity === 'medium').length;
  const low = painPoints.filter((p) => p.severity === 'low').length;

  const highPct = Math.round((high / total) * 100);
  const medPct = Math.round((med / total) * 100);
  const lowPct = Math.round((low / total) * 100);

  const avgImpact = Math.round(painPoints.reduce((acc, p) => acc + (p.impact_score || 0), 0) / total);

  return (
    <div style={{ marginTop: '12px', padding: '12px 14px', backgroundColor: 'var(--bg)', borderRadius: '8px', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '12px' }}>
        <span style={{ fontWeight: 600, color: 'var(--text)' }}>
          Severity Breakdown ({total} Active Issues)
        </span>
        <span style={{ color: 'var(--text-muted)' }}>
          Avg Friction Impact Score: <strong style={{ color: '#A8534C' }}>{avgImpact}/100</strong>
        </span>
      </div>

      {/* Stacked Bar */}
      <div style={{ height: '10px', borderRadius: '5px', overflow: 'hidden', display: 'flex', backgroundColor: 'var(--border)' }}>
        {high > 0 && (
          <div
            style={{ width: `${highPct}%`, backgroundColor: '#C62828', transition: 'width 0.3s ease' }}
            title={`High Severity: ${high} issues (${highPct}%)`}
          />
        )}
        {med > 0 && (
          <div
            style={{ width: `${medPct}%`, backgroundColor: '#B88232', transition: 'width 0.3s ease' }}
            title={`Medium Severity: ${med} issues (${medPct}%)`}
          />
        )}
        {low > 0 && (
          <div
            style={{ width: `${lowPct}%`, backgroundColor: '#355C52', transition: 'width 0.3s ease' }}
            title={`Low Severity: ${low} issues (${lowPct}%)`}
          />
        )}
      </div>

      {/* Legend & Counts */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '11px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#C62828' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#C62828' }}></span>
          <strong>{high} High</strong> ({highPct}%)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#B88232' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#B88232' }}></span>
          <strong>{med} Medium</strong> ({medPct}%)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#355C52' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#355C52' }}></span>
          <strong>{low} Low</strong> ({lowPct}%)
        </div>
      </div>
    </div>
  );
}

/**
 * Ranked Feature Priority Bar Graph with Demand Badges and Explainability Popover
 */
export function FeaturePriorityChart({ clusters = [] }) {
  const [hoveredCluster, setHoveredCluster] = useState(null);

  if (!clusters || clusters.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
        No feature request clusters found.
      </div>
    );
  }

  // Display top 6 clusters
  const topClusters = clusters.slice(0, 6);

  const demandColors = {
    high: { bar: '#355C52', badgeBg: 'rgba(53, 92, 82, 0.12)', text: '#203C35' },
    medium: { bar: '#B88232', badgeBg: 'rgba(184, 130, 50, 0.12)', text: '#B88232' },
    low: { bar: '#707570', badgeBg: 'rgba(112, 117, 112, 0.12)', text: '#707570' },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', position: 'relative' }}>
      {topClusters.map((cluster) => {
        const colors = demandColors[cluster.demand_level] || demandColors.medium;
        const score = cluster.priority_score || 0;
        const isHovered = hoveredCluster?.id === cluster.id;

        return (
          <div
            key={cluster.id}
            onMouseEnter={() => setHoveredCluster(cluster)}
            onMouseLeave={() => setHoveredCluster(null)}
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              border: `1px solid ${isHovered ? colors.bar : 'var(--border)'}`,
              backgroundColor: isHovered ? 'var(--bg-card)' : 'var(--bg)',
              boxShadow: isHovered ? 'var(--shadow-md)' : 'none',
              transition: 'all 0.2s ease',
              cursor: 'pointer',
            }}
          >
            {/* Header: Name, Demand Badge, Priority Score */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: '13px' }}>
                  {cluster.cluster_name}
                </span>
                <span
                  style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    backgroundColor: colors.badgeBg,
                    color: colors.text,
                  }}
                >
                  {cluster.demand_level} Demand
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Priority:</span>
                <strong style={{ fontSize: '14px', color: colors.bar }}>{score}/100</strong>
              </div>
            </div>

            {/* Horizontal Bar */}
            <div style={{ height: '8px', backgroundColor: 'var(--border)', borderRadius: '4px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${score}%`,
                  height: '100%',
                  backgroundColor: colors.bar,
                  borderRadius: '4px',
                  transition: 'width 0.4s ease',
                }}
              />
            </div>

            {/* Subtext: Counts & Breadth */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
              <span>{cluster.request_count} requests • {cluster.unique_customers_count || cluster.request_count} unique users</span>
              {isHovered && cluster.score_breakdown && (
                <span style={{ color: 'var(--text)', fontWeight: 500 }}>
                  {cluster.score_breakdown.formula_weights}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
