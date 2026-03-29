import React, { useEffect, useState } from 'react';
import { listModels } from '../../api/ai';
import type { ModelInfo } from '../../types/chat';

interface ModelSelectorProps {
  provider: string;
  model: string;
  onSelect: (provider: string, model: string) => void;
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
    return <div className="text-xs text-gray-400">Loading models...</div>;
  }

  return (
    <div className="flex items-center gap-2">
      <select
        value={`${provider}:${model}`}
        onChange={(e) => {
          const [p, ...rest] = e.target.value.split(':');
          onSelect(p, rest.join(':'));
        }}
        className="text-xs bg-gray-100 border border-gray-200 rounded-lg px-2 py-1.5 focus:ring-1 focus:ring-primary-500 outline-none"
      >
        {models.map((m) =>
          m.is_available ? (
            m.models.map((modelName) => (
              <option key={`${m.provider}:${modelName}`} value={`${m.provider}:${modelName}`}>
                {m.provider}/{modelName}
              </option>
            ))
          ) : (
            <option key={m.provider} disabled value={`${m.provider}:`}>
              {m.provider} (unavailable)
            </option>
          )
        )}
        {/* Fallback options when API is unreachable */}
        {models.length === 0 && (
          <>
            <option value="ollama:llama3.1">ollama/llama3.1</option>
            <option value="openai:gpt-4o">openai/gpt-4o</option>
            <option value="claude:claude-sonnet-4-20250514">claude/claude-sonnet-4-20250514</option>
          </>
        )}
      </select>
    </div>
  );
}
