import React, { useState } from 'react';
import type { TableComponent } from '../../types/chat';

type TableCell = string | number | null;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function normalizeLookupKey(value: string): string {
  return value
    .trim()
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase();
}

function toCamelCaseKey(value: string): string {
  const normalized = normalizeLookupKey(value);
  return normalized.replace(/_([a-z0-9])/g, (_, char: string) => char.toUpperCase());
}

function getRecordCell(row: Record<string, unknown>, columnLabel: string): unknown {
  const trimmedLabel = columnLabel.trim();
  const normalizedLabel = normalizeLookupKey(trimmedLabel);
  const compactLabel = normalizedLabel.replace(/_/g, '');
  const directCandidates = [
    columnLabel,
    trimmedLabel,
    normalizedLabel,
    toCamelCaseKey(trimmedLabel),
    compactLabel,
  ];

  for (const candidate of directCandidates) {
    if (candidate && Object.prototype.hasOwnProperty.call(row, candidate)) {
      return row[candidate];
    }
  }

  for (const [key, value] of Object.entries(row)) {
    const normalizedKey = normalizeLookupKey(key);
    if (
      key.trim().toLowerCase() === trimmedLabel.toLowerCase() ||
      normalizedKey === normalizedLabel ||
      normalizedKey.replace(/_/g, '') === compactLabel
    ) {
      return value;
    }
  }

  return null;
}

function alignRowCells(cells: TableCell[], columnCount: number): TableCell[] {
  if (columnCount === 0) {
    return cells;
  }

  return Array.from({ length: columnCount }, (_, index) => cells[index] ?? null);
}

function normalizeCell(value: unknown): TableCell {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === 'string' || typeof value === 'number') {
    return value;
  }
  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }
  return JSON.stringify(value);
}

export default function DataTable({ component }: { component: TableComponent }) {
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  const rawRows: unknown[] = Array.isArray(component.rows) ? (component.rows as unknown[]) : [];
  const firstObjectRow = rawRows.find(isRecord);
  const derivedColumns =
    component.columns.length > 0
      ? component.columns
      : firstObjectRow
        ? Object.keys(firstObjectRow)
        : [];

  const normalizedRows: TableCell[][] = rawRows.map((row) => {
    if (Array.isArray(row)) {
      return alignRowCells(row.map(normalizeCell), derivedColumns.length);
    }

    if (isRecord(row)) {
      const keys = derivedColumns.length > 0 ? derivedColumns : Object.keys(row);
      return keys.map((key) => normalizeCell(getRecordCell(row, key)));
    }

    return alignRowCells([normalizeCell(row)], derivedColumns.length);
  });

  const handleSort = (colIdx: number) => {
    if (sortCol === colIdx) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(colIdx);
      setSortAsc(true);
    }
  };

  const sortedRows = [...normalizedRows];
  if (sortCol !== null) {
    sortedRows.sort((a, b) => {
      const va = a[sortCol] ?? '';
      const vb = b[sortCol] ?? '';
      const cmp = String(va).localeCompare(String(vb), undefined, { numeric: true });
      return sortAsc ? cmp : -cmp;
    });
  }

  return (
    <div className="ops-card-soft overflow-hidden rounded-xl">
      {component.title && (
        <div className="border-b border-[var(--ops-line-soft)] px-4 py-3 text-sm font-semibold text-[var(--ops-text)]">
          {component.title}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[rgba(255,255,255,0.03)]">
              {derivedColumns.map((col, idx) => (
                <th
                  key={idx}
                  onClick={() => handleSort(idx)}
                  className="cursor-pointer select-none px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-[var(--ops-text-muted)] transition hover:bg-[rgba(255,255,255,0.04)]"
                >
                  <span className="flex items-center gap-1">
                    {col}
                    {sortCol === idx && (
                      <span className="text-[var(--ops-highlight)]">{sortAsc ? '\u2191' : '\u2193'}</span>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--ops-line-softer)]">
            {sortedRows.map((row, rIdx) => (
              <tr key={rIdx} className="transition hover:bg-[var(--ops-row-hover)]">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="whitespace-nowrap px-4 py-2.5 text-[var(--ops-text-muted)]">
                    {cell !== null && cell !== undefined ? String(cell) : '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="border-t border-[var(--ops-line-soft)] px-4 py-2 text-xs text-[var(--ops-text-soft)]">
        {normalizedRows.length} row{normalizedRows.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
}
