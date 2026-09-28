import React, { useState } from 'react';
import { accent, palette, sentiment, severity, demand, getCategoryColor } from '../theme';
import { Segmented } from './ui';

/**
 * Clean SVG Donut Chart for Sentiment Breakdown with Center Health Metric
 */
export function SentimentDonutChart({ positive = 0, neutral = 0, negative = 0, healthScore = null }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  const total = (positive || 0) + (neutral || 0) + (negative || 0);
  const data = [
    { label: 'Positive', count: positive, color: sentiment.positive.line, bg: sentiment.positive.soft },
    { label: 'Neutral', count: neutral, color: sentiment.neutral.line, bg: sentiment.neutral.soft },
    { label: 'Negative', count: negative, color: sentiment.negative.line, bg: sentiment.negative.soft },
  ];

  if (total === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 'var(--sp-4)', color: 'var(--text-muted)' }}>
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
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--sp-3)', width: '100%' }}>
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
              <span style={{ fontSize: 'var(--fs-lg)', fontWeight: 700, color: activeSlice.color }}>
                {activeSlice.percent}%
              </span>
              <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', fontWeight: 600 }}>
                {activeSlice.label} ({activeSlice.count})
              </span>
            </>
          ) : (
            <>
              <span style={{ fontSize: 'var(--fs-xl)', fontWeight: 800, color: 'var(--text)' }}>
                {healthScore !== null ? `${healthScore}%` : `${slices[0].percent}%`}
              </span>
              <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Health Score
              </span>
            </>
          )}
        </div>
      </div>

      {/* Legend Chips */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--sp-3)', flexWrap: 'wrap', width: '100%' }}>
        {slices.map((slice) => (
          <div
            key={slice.label}
            onMouseEnter={() => setHoveredIndex(slice.idx)}
            onMouseLeave={() => setHoveredIndex(null)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--sp-2)',
              padding: 'var(--sp-2) var(--sp-3)',
              borderRadius: 'var(--radius-full)',
              backgroundColor: hoveredIndex === slice.idx ? slice.bg : 'var(--bg)',
              border: `1px solid ${hoveredIndex === slice.idx ? slice.color : 'var(--border)'}`,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              fontSize: 'var(--fs-xs)',
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
      <div style={{ textAlign: 'center', padding: 'var(--sp-4)', color: 'var(--text-muted)' }}>
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)', width: '100%' }}>
      {/* View switcher — the kit's segmented control, so every view toggle in the app matches. */}
      <Segmented
        className="segmented-center"
        label="Category chart view"
        value={viewMode}
        onChange={setViewMode}
        options={[
          { value: 'donut', label: 'Donut', icon: 'dot' },
          { value: 'bars', label: 'Bars', icon: 'barChart' },
          { value: 'grid', label: 'Grid', icon: 'grid' },
        ]}
      />

      {/* MODE 1: DONUT VIEW */}
      {viewMode === 'donut' && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--sp-3)', width: '100%' }}>
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
                padding: 'var(--sp-3)',
                textAlign: 'center',
              }}
            >
              {activeSlice ? (
                <>
                  <span style={{ fontSize: 'var(--fs-lg)', fontWeight: 800, color: activeSlice.color }}>
                    {activeSlice.percent}%
                  </span>
                  <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text)', fontWeight: 600, textTransform: 'capitalize' }}>
                    {activeSlice.label}
                  </span>
                  <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
                    ({activeSlice.count} items)
                  </span>
                </>
              ) : (
                <>
                  <span style={{ fontSize: 'var(--fs-xl)', fontWeight: 800, color: 'var(--text)' }}>
                    {total}
                  </span>
                  <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', fontWeight: 600 }}>
                    Total Items
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Category Progress List under Donut */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)', width: '100%', marginTop: 'var(--sp-1)' }}>
            {slices.map((slice) => (
              <div
                key={slice.category}
                onMouseEnter={() => setHoveredCategory(slice.category)}
                onMouseLeave={() => setHoveredCategory(null)}
                onClick={() => onSelectCategory && onSelectCategory(slice.category)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--sp-1)',
                  cursor: 'pointer',
                  opacity: hoveredCategory === null || hoveredCategory === slice.category ? 1 : 0.5,
                  transition: 'opacity 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 'var(--sp-2)',
                      padding: 'var(--sp-1) var(--sp-2)',
                      borderRadius: 'var(--radius-lg)',
                      backgroundColor: `${slice.color}14`,
                      border: `1px solid ${slice.color}40`,
                      fontSize: 'var(--fs-xs)',
                      fontWeight: 600,
                      color: slice.color,
                      textTransform: 'lowercase',
                    }}
                  >
                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: slice.color }}></span>
                    {slice.label}
                  </div>
                  <span style={{ fontSize: 'var(--fs-xs)', fontWeight: 600, color: 'var(--text-muted)' }}>
                    {slice.count} <span style={{ fontWeight: 400, fontSize: 'var(--fs-xs)' }}>({slice.percent}%)</span>
                  </span>
                </div>
                <div style={{ height: '5px', width: '100%', backgroundColor: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${slice.percent}%`,
                      backgroundColor: slice.color,
                      borderRadius: 'var(--radius-sm)',
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODE 2: RANKED BARS VIEW */}
      {viewMode === 'bars' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)', width: '100%', padding: 'var(--sp-1) 0' }}>
          {slices.map((slice) => (
            <div
              key={slice.category}
              onMouseEnter={() => setHoveredCategory(slice.category)}
              onMouseLeave={() => setHoveredCategory(null)}
              onClick={() => onSelectCategory && onSelectCategory(slice.category)}
              style={{
                padding: 'var(--sp-2) var(--sp-3)',
                borderRadius: 'var(--radius)',
                backgroundColor: hoveredCategory === slice.category ? `${slice.color}10` : 'var(--bg)',
                border: `1px solid ${hoveredCategory === slice.category ? slice.color : 'var(--border)'}`,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-2)', fontSize: 'var(--fs-xs)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: slice.color }}></span>
                  <strong style={{ color: 'var(--text)', textTransform: 'capitalize' }}>{slice.label}</strong>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
                  <span style={{ fontWeight: 700, color: slice.color }}>{slice.percent}%</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-xs)' }}>({slice.count} items)</span>
                </div>
              </div>
              <div style={{ height: '7px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--border)', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${slice.percent}%`,
                    height: '100%',
                    backgroundColor: slice.color,
                    borderRadius: 'var(--radius-sm)',
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
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 'var(--sp-2)', width: '100%' }}>
          {slices.map((slice) => (
            <div
              key={slice.category}
              onMouseEnter={() => setHoveredCategory(slice.category)}
              onMouseLeave={() => setHoveredCategory(null)}
              onClick={() => onSelectCategory && onSelectCategory(slice.category)}
              style={{
                padding: 'var(--sp-3) var(--sp-2)',
                borderRadius: 'var(--radius)',
                backgroundColor: hoveredCategory === slice.category ? `${slice.color}15` : 'var(--bg)',
                border: `1px solid ${hoveredCategory === slice.category ? slice.color : 'var(--border)'}`,
                borderTop: `3px solid ${slice.color}`,
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'capitalize', marginBottom: 'var(--sp-1)' }}>
                {slice.label}
              </div>
              <div style={{ fontSize: 'var(--fs-lg)', fontWeight: 800, color: slice.color }}>
                {slice.count}
              </div>
              <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 600, color: 'var(--text)', marginTop: 'var(--sp-1)' }}>
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
      <div style={{ textAlign: 'center', padding: 'var(--sp-5)', color: 'var(--text-muted)' }}>
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
              <stop offset="0%" stopColor={accent.line} stopOpacity="0.18" />
              <stop offset="100%" stopColor={accent.line} stopOpacity="0.01" />
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
          <path d={totalLine} fill="none" stroke={accent.line} strokeWidth="2.5" />
          <path d={posLine} fill="none" stroke={sentiment.positive.line} strokeWidth="2" strokeDasharray="5 3" />
          <path d={negLine} fill="none" stroke={sentiment.negative.line} strokeWidth="2" strokeDasharray="5 3" />

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
                    stroke={accent.line}
                    strokeWidth="1.5"
                    strokeDasharray="3 3"
                  />
                )}

                {/* Point circle */}
                <circle
                  cx={x}
                  cy={y}
                  r={isHovered ? 6 : 4}
                  fill={isHovered ? accent.strong : accent.line}
                  stroke={palette.surface}
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
              borderRadius: 'var(--radius)',
              padding: 'var(--sp-2) var(--sp-3)',
              boxShadow: 'var(--shadow-md)',
              fontSize: 'var(--fs-xs)',
              zIndex: 10,
              pointerEvents: 'none',
              minWidth: '180px',
            }}
          >
            <div style={{ fontWeight: 700, color: 'var(--text)', marginBottom: 'var(--sp-1)' }}>
              {hoveredPoint.period}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', margin: 'var(--sp-1) 0' }}>
              <span style={{ color: accent.line, fontWeight: 600 }}>Total Volume:</span>
              <strong>{hoveredPoint.total_count}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', margin: 'var(--sp-1) 0' }}>
              <span style={{ color: sentiment.positive.line }}>Positive:</span>
              <span>{hoveredPoint.positive_count}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', margin: 'var(--sp-1) 0' }}>
              <span style={{ color: sentiment.neutral.line }}>Neutral:</span>
              <span>{hoveredPoint.neutral_count}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', margin: 'var(--sp-1) 0' }}>
              <span style={{ color: sentiment.negative.line }}>Negative:</span>
              <span>{hoveredPoint.negative_count}</span>
            </div>
            {hoveredPoint.top_category && (
              <div style={{ marginTop: 'var(--sp-2)', paddingTop: 'var(--sp-1)', borderTop: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                Top: <strong>{hoveredPoint.top_category.replace(/_/g, ' ')}</strong>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Graph Legend */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--sp-4)', marginTop: 'var(--sp-2)', fontSize: 'var(--fs-xs)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
          <span style={{ width: '16px', height: '3px', backgroundColor: accent.line, display: 'inline-block' }}></span>
          <span style={{ color: 'var(--text)', fontWeight: 600 }}>Total Feedback Volume</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
          <span style={{ width: '16px', height: '2px', backgroundColor: sentiment.positive.line, display: 'inline-block' }}></span>
          <span style={{ color: 'var(--text-muted)' }}>Positive Trajectory</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
          <span style={{ width: '16px', height: '2px', backgroundColor: sentiment.negative.line, display: 'inline-block' }}></span>
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
    <div style={{ marginTop: 'var(--sp-3)', padding: 'var(--sp-3)', backgroundColor: 'var(--bg)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-2)', fontSize: 'var(--fs-xs)' }}>
        <span style={{ fontWeight: 600, color: 'var(--text)' }}>
          Severity Breakdown ({total} Active Issues)
        </span>
        <span style={{ color: 'var(--text-muted)' }}>
          Avg Friction Impact Score: <strong style={{ color: 'var(--text)' }}>{avgImpact}/100</strong>
        </span>
      </div>

      {/* Stacked Bar */}
      <div style={{ height: '10px', borderRadius: 'var(--radius-sm)', overflow: 'hidden', display: 'flex', backgroundColor: 'var(--border)' }}>
        {high > 0 && (
          <div
            style={{ width: `${highPct}%`, backgroundColor: severity.high.line, transition: 'width 0.3s ease' }}
            title={`High Severity: ${high} issues (${highPct}%)`}
          />
        )}
        {med > 0 && (
          <div
            style={{ width: `${medPct}%`, backgroundColor: severity.medium.line, transition: 'width 0.3s ease' }}
            title={`Medium Severity: ${med} issues (${medPct}%)`}
          />
        )}
        {low > 0 && (
          <div
            style={{ width: `${lowPct}%`, backgroundColor: severity.low.line, transition: 'width 0.3s ease' }}
            title={`Low Severity: ${low} issues (${lowPct}%)`}
          />
        )}
      </div>

      {/* Legend & Counts */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--sp-2)', fontSize: 'var(--fs-xs)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)', color: severity.high.line }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: severity.high.line }}></span>
          <strong>{high} High</strong> ({highPct}%)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)', color: severity.medium.line }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: severity.medium.line }}></span>
          <strong>{med} Medium</strong> ({medPct}%)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)', color: severity.low.line }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: severity.low.line }}></span>
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
      <div style={{ textAlign: 'center', padding: 'var(--sp-4)', color: 'var(--text-muted)' }}>
        No feature request clusters found.
      </div>
    );
  }

  // Display top 6 clusters
  const topClusters = clusters.slice(0, 6);

  const demandColors = {
    high: { bar: demand.high.line, badgeBg: demand.high.soft, text: demand.high.line },
    medium: { bar: demand.medium.line, badgeBg: demand.medium.soft, text: demand.medium.line },
    low: { bar: demand.low.line, badgeBg: demand.low.soft, text: demand.low.line },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)', width: '100%', position: 'relative' }}>
      {topClusters.map((cluster) => {
        const colors = demandColors[cluster.demand_level] || demandColors.medium;
        const score = cluster.priority_score || 0;
        const isHovered = hoveredCluster?.id === cluster.id;
        const reqCount = cluster.request_count || 0;
        const userCount = cluster.unique_customers_count || reqCount;

        return (
          <div
            key={cluster.id}
            onMouseEnter={() => setHoveredCluster(cluster)}
            onMouseLeave={() => setHoveredCluster(null)}
            style={{
              padding: 'var(--sp-2) var(--sp-3)',
              borderRadius: 'var(--radius)',
              border: `1px solid ${isHovered ? colors.bar : 'var(--border)'}`,
              backgroundColor: isHovered ? 'var(--bg-card)' : 'var(--bg)',
              boxShadow: isHovered ? 'var(--shadow-md)' : 'none',
              transition: 'all 0.2s ease',
              cursor: 'pointer',
            }}
          >
            {/* Header: Name, Demand Badge, Priority Score */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
                <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: 'var(--fs-sm)' }}>
                  {cluster.cluster_name}
                </span>
                <span
                  style={{
                    fontSize: 'var(--fs-xs)',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    padding: 'var(--sp-1) var(--sp-2)',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: colors.badgeBg,
                    color: colors.text,
                  }}
                >
                  {cluster.demand_level} Demand
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
                <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>Priority:</span>
                <strong style={{ fontSize: 'var(--fs-sm)', color: colors.bar }}>{score}/100</strong>
              </div>
            </div>

            {/* Horizontal Bar */}
            <div style={{ height: '8px', backgroundColor: 'var(--border)', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${score}%`,
                  height: '100%',
                  backgroundColor: colors.bar,
                  borderRadius: 'var(--radius-sm)',
                  transition: 'width 0.4s ease',
                }}
              />
            </div>

            {/* Subtext: Counts & Breadth */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--sp-2)', fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
              <span>
                {reqCount} {reqCount === 1 ? 'request' : 'requests'} • {userCount} {userCount === 1 ? 'unique user' : 'unique users'}
              </span>
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

