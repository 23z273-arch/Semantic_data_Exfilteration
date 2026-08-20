import React from 'react';

export default function RiskGauge({ score }) {
  const percentage = Math.round(score * 100);
  
  // Color selection based on score
  let strokeColor = 'var(--success)';
  if (score >= 0.75) {
    strokeColor = 'var(--danger)';
  } else if (score >= 0.50) {
    strokeColor = 'var(--warning)';
  }

  // SVG Circular progress configurations
  const radius = 60;
  const strokeWidth = 8;
  const normalizedRadius = radius - strokeWidth * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score * circumference);

  return (
    <div className="gauge-container">
      <div className="gauge-svg-box">
        <svg height="150" width="150" style={{ transform: 'rotate(-90deg)' }}>
          {/* Background circle */}
          <circle
            stroke="rgba(255, 255, 255, 0.03)"
            fill="transparent"
            strokeWidth={strokeWidth}
            r={normalizedRadius}
            cx="75"
            cy="75"
          />
          {/* Active progress circle */}
          <circle
            stroke={strokeColor}
            fill="transparent"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference + ' ' + circumference}
            style={{ strokeDashoffset, transition: 'stroke-dashoffset 0.35s' }}
            r={normalizedRadius}
            cx="75"
            cy="75"
          />
        </svg>
        <div className="gauge-text">
          <span className="gauge-percentage" style={{ color: strokeColor }}>
            {percentage}%
          </span>
          <span className="gauge-label">Risk</span>
        </div>
      </div>
    </div>
  );
}
