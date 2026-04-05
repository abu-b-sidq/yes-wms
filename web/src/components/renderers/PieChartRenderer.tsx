import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { PieChartComponent } from '../../types/chat';

const COLORS = ['#79bf64', '#d4ea72', '#76b0ff', '#ef7c74', '#bf9bff', '#f2c162', '#65c186', '#5f9f4e'];

export default function PieChartRenderer({ component }: { component: PieChartComponent }) {
  return (
    <div className="ops-card-soft rounded-xl p-4">
      {component.title && (
        <div className="mb-4 text-sm font-semibold text-[var(--ops-text)]">{component.title}</div>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={component.data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
          >
            {component.data.map((_, idx) => (
              <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
