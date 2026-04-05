import React from 'react';
import type { StatCardComponent } from '../../types/chat';

export default function StatCard({ component }: { component: StatCardComponent }) {
  return (
    <div className="ops-note-card rounded-xl p-5">
      <div className="mb-1 text-sm font-medium text-[var(--ops-highlight)]">{component.label}</div>
      <div className="text-3xl font-bold text-[var(--ops-text)]">{component.value}</div>
      {component.description && (
        <div className="mt-1 text-sm text-[var(--ops-text-muted)]">{component.description}</div>
      )}
      {component.trend && (
        <div className="mt-1 text-sm font-medium text-[var(--ops-success)]">{component.trend}</div>
      )}
    </div>
  );
}
