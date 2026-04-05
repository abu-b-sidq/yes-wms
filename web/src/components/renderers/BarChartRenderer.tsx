import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { BarChartComponent } from '../../types/chat';

export default function BarChartRenderer({ component }: { component: BarChartComponent }) {
  return (
    <div className="ops-card-soft rounded-xl p-4">
      {component.title && (
        <div className="mb-4 text-sm font-semibold text-[var(--ops-text)]">{component.title}</div>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={component.data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--ops-chart-grid)" />
          <XAxis
            dataKey={component.x_key}
            tick={{ fontSize: 12, fill: 'var(--ops-text-soft)' }}
            axisLine={{ stroke: 'var(--ops-line-soft)' }}
            tickLine={{ stroke: 'var(--ops-line-soft)' }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: 'var(--ops-text-soft)' }}
            axisLine={{ stroke: 'var(--ops-line-soft)' }}
            tickLine={{ stroke: 'var(--ops-line-soft)' }}
          />
          <Tooltip />
          <Bar dataKey={component.y_key} fill="#79bf64" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
