import React, { useState } from 'react';
import type { FormComponent } from '../../types/chat';

interface FormRendererProps {
  component: FormComponent;
  onConfirm?: (action: string, parameters: Record<string, unknown>) => void;
}

export default function FormRenderer({ component, onConfirm }: FormRendererProps) {
  const [values, setValues] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    for (const field of component.fields) {
      initial[field.name] = field.default_value || '';
    }
    return initial;
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConfirm?.(component.action, values);
  };

  return (
    <div className="ops-card-soft rounded-xl p-5">
      <h3 className="mb-4 text-sm font-semibold text-[var(--ops-text)]">{component.title}</h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        {component.fields.map((field) => (
          <div key={field.name}>
            <label className="mb-1 block text-sm font-medium text-[var(--ops-text-muted)]">
              {field.label}
              {field.required && <span className="ml-0.5 text-[var(--ops-danger)]">*</span>}
            </label>
            {field.type === 'select' && field.options ? (
              <select
                value={values[field.name]}
                onChange={(e) => setValues(v => ({ ...v, [field.name]: e.target.value }))}
                required={field.required}
                className="ops-input w-full rounded-lg px-3 py-2 text-sm outline-none"
              >
                <option value="">Select...</option>
                {field.options.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            ) : (
              <input
                type={field.type === 'number' ? 'number' : 'text'}
                value={values[field.name]}
                onChange={(e) => setValues(v => ({ ...v, [field.name]: e.target.value }))}
                required={field.required}
                className="ops-input w-full rounded-lg px-3 py-2 text-sm outline-none"
              />
            )}
          </div>
        ))}
        <button
          type="submit"
          className="ops-button-primary rounded-lg px-4 py-2 text-sm font-medium transition"
        >
          Submit
        </button>
      </form>
    </div>
  );
}
