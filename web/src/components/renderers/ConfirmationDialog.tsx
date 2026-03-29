import React from 'react';
import type { ConfirmationDialogComponent } from '../../types/chat';

interface ConfirmationDialogProps {
  component: ConfirmationDialogComponent;
  onConfirm?: (action: string, parameters: Record<string, unknown>) => void;
}

export default function ConfirmationDialog({ component, onConfirm }: ConfirmationDialogProps) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center">
          <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-amber-900 text-sm">{component.title}</h3>
          <p className="text-sm text-amber-800 mt-1">{component.description}</p>

          <div className="flex gap-2 mt-4">
            <button
              onClick={() => onConfirm?.(component.action, component.parameters)}
              className="px-4 py-2 bg-amber-600 text-white rounded-lg text-sm font-medium hover:bg-amber-700 transition"
            >
              Confirm
            </button>
            <button className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
