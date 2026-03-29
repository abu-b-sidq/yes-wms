import React from 'react';
import type { DetailCardComponent } from '../../types/chat';

export default function DetailCard({ component }: { component: DetailCardComponent }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {component.title && (
        <div className="px-4 py-3 border-b border-gray-100 font-semibold text-gray-800 text-sm">
          {component.title}
        </div>
      )}
      <dl className="divide-y divide-gray-100">
        {component.fields.map((field, idx) => (
          <div key={idx} className="px-4 py-2.5 flex justify-between gap-4">
            <dt className="text-sm text-gray-500 flex-shrink-0">{field.label}</dt>
            <dd className="text-sm text-gray-900 text-right break-all">{field.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
