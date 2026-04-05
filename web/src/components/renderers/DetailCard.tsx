import React from 'react';
import type { DetailCardComponent } from '../../types/chat';

export default function DetailCard({ component }: { component: DetailCardComponent }) {
  return (
    <div className="ops-card-soft overflow-hidden rounded-xl">
      {component.title && (
        <div className="border-b border-[var(--ops-line-soft)] px-4 py-3 text-sm font-semibold text-[var(--ops-text)]">
          {component.title}
        </div>
      )}
      <dl className="divide-y divide-[var(--ops-line-softer)]">
        {component.fields.map((field, idx) => (
          <div key={idx} className="px-4 py-2.5 flex justify-between gap-4">
            <dt className="flex-shrink-0 text-sm text-[var(--ops-text-muted)]">{field.label}</dt>
            <dd className="break-all text-right text-sm text-[var(--ops-text)]">{field.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
