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
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h3 className="font-semibold text-gray-800 text-sm mb-4">{component.title}</h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        {component.fields.map((field) => (
          <div key={field.name}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {field.label}
              {field.required && <span className="text-red-500 ml-0.5">*</span>}
            </label>
            {field.type === 'select' && field.options ? (
              <select
                value={values[field.name]}
                onChange={(e) => setValues(v => ({ ...v, [field.name]: e.target.value }))}
                required={field.required}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-1 focus:ring-primary-500 outline-none"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-1 focus:ring-primary-500 outline-none"
              />
            )}
          </div>
        ))}
        <button
          type="submit"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition"
        >
          Submit
        </button>
      </form>
    </div>
  );
}
