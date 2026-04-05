import React from 'react';
import { useTheme } from '../../theme/ThemeContext';

interface ThemeToggleProps {
  className?: string;
}

export default function ThemeToggle({ className = '' }: ThemeToggleProps) {
  const { resolved, toggleTheme } = useTheme();
  const isLight = resolved === 'light';
  const nextModeLabel = isLight ? 'dark' : 'light';

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${nextModeLabel} mode`}
      title={`Switch to ${nextModeLabel} mode`}
      className={`ops-button-secondary inline-flex items-center gap-2 rounded-[18px] px-3 py-2.5 text-sm font-medium transition ${className}`}
    >
      <span className="flex h-8 w-8 items-center justify-center rounded-[14px] bg-[var(--ops-glass-soft)]">
        {isLight ? (
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 12.79A9 9 0 1 1 11.21 3c0 .24-.01.48-.01.72A9 9 0 0 0 20.28 12c.24 0 .48-.01.72-.01Z" />
          </svg>
        ) : (
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
            <circle cx="12" cy="12" r="4" />
            <path strokeLinecap="round" d="M12 2v2.5M12 19.5V22M4.93 4.93l1.77 1.77M17.3 17.3l1.77 1.77M2 12h2.5M19.5 12H22M4.93 19.07l1.77-1.77M17.3 6.7l1.77-1.77" />
          </svg>
        )}
      </span>
      <span className="hidden sm:inline">{isLight ? 'Light mode' : 'Dark mode'}</span>
    </button>
  );
}
