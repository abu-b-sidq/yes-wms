import React from 'react';
import type { StatCardComponent } from '../../types/chat';

export default function StatCard({ component }: { component: StatCardComponent }) {
  return (
    <div className="bg-gradient-to-br from-primary-50 to-white border border-primary-100 rounded-xl p-5">
      <div className="text-sm font-medium text-primary-600 mb-1">{component.label}</div>
      <div className="text-3xl font-bold text-gray-900">{component.value}</div>
      {component.description && (
        <div className="text-sm text-gray-500 mt-1">{component.description}</div>
      )}
      {component.trend && (
        <div className="text-sm font-medium text-green-600 mt-1">{component.trend}</div>
      )}
    </div>
  );
}
