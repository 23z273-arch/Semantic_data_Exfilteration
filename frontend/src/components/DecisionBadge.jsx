import React from 'react';

export default function DecisionBadge({ decision }) {
  const d = decision ? decision.toUpperCase() : 'ALLOW';
  
  if (d === 'BLOCK') {
    return <span className="badge badge-block">Block</span>;
  }
  if (d === 'WARN') {
    return <span className="badge badge-warn">Warn</span>;
  }
  return <span className="badge badge-allow">Allow</span>;
}
