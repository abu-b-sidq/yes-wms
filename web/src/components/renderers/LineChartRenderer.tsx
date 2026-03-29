import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { LineChartComponent } from '../../types/chat';

export default function LineChartRenderer({ component }: { component: LineChartComponent }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      {component.title && (
        <div className="font-semibold text-gray-800 text-sm mb-4">{component.title}</div>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={component.data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey={component.x_key} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey={component.y_key}
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 4, fill: '#3b82f6' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
