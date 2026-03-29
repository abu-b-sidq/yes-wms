import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { BarChartComponent } from '../../types/chat';

export default function BarChartRenderer({ component }: { component: BarChartComponent }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      {component.title && (
        <div className="font-semibold text-gray-800 text-sm mb-4">{component.title}</div>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={component.data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey={component.x_key} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey={component.y_key} fill="#3b82f6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
