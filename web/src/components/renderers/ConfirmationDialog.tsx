import React from 'react';
import type { ConfirmationDialogComponent } from '../../types/chat';

interface ConfirmationDialogProps {
  component: ConfirmationDialogComponent;
  onConfirm?: (action: string, parameters: Record<string, unknown>) => void;
}

export default function ConfirmationDialog({ component, onConfirm }: ConfirmationDialogProps) {
  return (
    <div className="ops-warning-card rounded-xl p-5">
      <div className="flex items-start gap-3">
        <div className="ops-warning-icon flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full">
          <svg className="h-4 w-4 text-[var(--ops-warning)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-[var(--ops-text)]">{component.title}</h3>
          <p className="mt-1 text-sm text-[var(--ops-text-muted)]">{component.description}</p>

          <div className="flex gap-2 mt-4">
            <button
              onClick={() => onConfirm?.(component.action, component.parameters)}
              className="ops-button-primary rounded-lg px-4 py-2 text-sm font-medium transition"
            >
              Confirm
            </button>
            <button className="ops-button-secondary rounded-lg px-4 py-2 text-sm font-medium transition">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
