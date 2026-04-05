import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { LineChartComponent } from '../../types/chat';

export default function LineChartRenderer({ component }: { component: LineChartComponent }) {
  return (
    <div className="ops-card-soft rounded-xl p-4">
      {component.title && (
        <div className="mb-4 text-sm font-semibold text-[var(--ops-text)]">{component.title}</div>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={component.data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
          <XAxis dataKey={component.x_key} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey={component.y_key}
            stroke="#79bf64"
            strokeWidth={2}
            dot={{ r: 4, fill: '#79bf64' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
