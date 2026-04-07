import React, { useEffect, useState } from 'react';
import { listModels } from '../../api/ai';
import type { ModelInfo } from '../../types/chat';

interface ModelSelectorProps {
  provider: string;
  model: string;
  onSelect: (provider: string, model: string) => void;
}

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export default function ModelSelector({ provider, model, onSelect }: ModelSelectorProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listModels()
      .then(setModels)
      .catch(() => setModels([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-xs text-[var(--ops-text-soft)]">Loading models...</div>;
  }

  const selectedValue = `${provider}:${model}`;
  const fallbackOptions: SelectOption[] = [
    { value: 'ollama:llama3.1', label: 'ollama/llama3.1' },
    { value: 'openai:gpt-4o', label: 'openai/gpt-4o' },
    { value: 'claude:claude-sonnet-4-20250514', label: 'claude/claude-sonnet-4-20250514' },
    { value: 'deepagent:claude-sonnet-4-20250514', label: 'deepagent/claude-sonnet-4-20250514' },
  ];
  const discoveredOptions: SelectOption[] = models.flatMap((entry) =>
    entry.is_available
      ? entry.models.map((modelName) => ({
          value: `${entry.provider}:${modelName}`,
          label: `${entry.provider}/${modelName}`,
        }))
      : [
          {
            value: `${entry.provider}:`,
            label: `${entry.provider} (unavailable)`,
            disabled: true,
          },
        ]
  );
  const options = (models.length === 0 ? fallbackOptions : discoveredOptions).slice();

  if (!options.some((option) => option.value === selectedValue)) {
    options.unshift({
      value: selectedValue,
      label: `${provider}/${model}`,
    });
  }

  return (
    <div className="ops-input-shell flex items-center gap-2 rounded-[18px] px-3 py-2">
      <span className="ops-label text-[11px]">
        Model
      </span>
      <select
        value={selectedValue}
        onChange={(e) => {
          const [nextProvider, ...rest] = e.target.value.split(':');
          onSelect(nextProvider, rest.join(':'));
        }}
        className="rounded-full bg-transparent pr-6 text-xs font-medium text-[var(--ops-text)] outline-none"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value} disabled={option.disabled}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
