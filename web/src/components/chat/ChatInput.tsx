import React, { useEffect, useRef, useState } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  variant?: 'dock' | 'hero';
}

export default function ChatInput({
  onSend,
  disabled,
  placeholder,
  variant = 'dock',
}: ChatInputProps) {
  const [text, setText] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const isHero = variant === 'hero';

  useEffect(() => {
    inputRef.current?.focus();
  }, [disabled]);

  const handleSubmit = () => {
    const trimmed = text.trim();

    if (!trimmed || disabled) {
      return;
    }

    onSend(trimmed);
    setText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      className={
        isHero
          ? 'ops-input-shell rounded-[28px] p-4'
          : 'ops-dock-shell p-3.5'
      }
    >
      <div className={isHero ? '' : 'mx-auto flex max-w-4xl items-end gap-3'}>
        <textarea
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={isHero ? 3 : 1}
          placeholder={placeholder || 'Ask anything about your warehouse...'}
          className={`ops-input w-full resize-none text-sm leading-7 outline-none transition disabled:cursor-not-allowed disabled:opacity-50 ${
            isHero
              ? 'min-h-[120px] rounded-[24px] px-4 py-3.5 text-sm'
              : 'max-h-32 rounded-[22px] px-4 py-3.5'
          }`}
          style={{ minHeight: isHero ? '120px' : '52px' }}
        />

        <div className={isHero ? 'mt-3 flex flex-wrap items-center justify-between gap-3' : ''}>
          <button
            onClick={handleSubmit}
            disabled={disabled || !text.trim()}
            className={`ops-button-primary flex items-center justify-center gap-2 rounded-[20px] font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${
              isHero
                ? 'min-w-[132px] px-5 py-3'
                : 'shrink-0 px-5 py-3'
            }`}
          >
            <span>{isHero ? 'Send request' : 'Send'}</span>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
