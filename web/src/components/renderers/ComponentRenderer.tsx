import React from 'react';
import type { UIComponent } from '../../types/chat';
import StatCard from './StatCard';
import DataTable from './DataTable';
import BarChartRenderer from './BarChartRenderer';
import PieChartRenderer from './PieChartRenderer';
import LineChartRenderer from './LineChartRenderer';
import DetailCard from './DetailCard';
import ConfirmationDialog from './ConfirmationDialog';
import FormRenderer from './FormRenderer';

interface ComponentRendererProps {
  component: UIComponent;
  onConfirmAction?: (action: string, parameters: Record<string, unknown>) => void;
}

export default function ComponentRenderer({ component, onConfirmAction }: ComponentRendererProps) {
  switch (component.type) {
    case 'stat_card':
      return <StatCard component={component} />;
    case 'table':
      return <DataTable component={component} />;
    case 'bar_chart':
      return <BarChartRenderer component={component} />;
    case 'pie_chart':
      return <PieChartRenderer component={component} />;
    case 'line_chart':
      return <LineChartRenderer component={component} />;
    case 'detail_card':
      return <DetailCard component={component} />;
    case 'confirmation_dialog':
      return <ConfirmationDialog component={component} onConfirm={onConfirmAction} />;
    case 'form':
      return <FormRenderer component={component} onConfirm={onConfirmAction} />;
    default:
      return (
        <div className="rounded-xl border border-[var(--ops-border)] bg-[rgba(255,255,255,0.03)] p-4 text-sm text-[var(--ops-text-muted)]">
          Unknown component type: {(component as { type: string }).type}
        </div>
      );
  }
}
