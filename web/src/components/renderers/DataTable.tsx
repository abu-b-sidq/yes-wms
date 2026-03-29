import React, { useState } from 'react';
import type { TableComponent } from '../../types/chat';

export default function DataTable({ component }: { component: TableComponent }) {
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  const handleSort = (colIdx: number) => {
    if (sortCol === colIdx) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(colIdx);
      setSortAsc(true);
    }
  };

  const sortedRows = [...component.rows];
  if (sortCol !== null) {
    sortedRows.sort((a, b) => {
      const va = a[sortCol] ?? '';
      const vb = b[sortCol] ?? '';
      const cmp = String(va).localeCompare(String(vb), undefined, { numeric: true });
      return sortAsc ? cmp : -cmp;
    });
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {component.title && (
        <div className="px-4 py-3 border-b border-gray-100 font-semibold text-gray-800 text-sm">
          {component.title}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50">
              {component.columns.map((col, idx) => (
                <th
                  key={idx}
                  onClick={() => handleSort(idx)}
                  className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition select-none"
                >
                  <span className="flex items-center gap-1">
                    {col}
                    {sortCol === idx && (
                      <span className="text-primary-500">{sortAsc ? '\u2191' : '\u2193'}</span>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sortedRows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-gray-50 transition">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="px-4 py-2.5 text-gray-700 whitespace-nowrap">
                    {cell !== null && cell !== undefined ? String(cell) : '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="px-4 py-2 text-xs text-gray-400 border-t border-gray-100">
        {component.rows.length} row{component.rows.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
}
