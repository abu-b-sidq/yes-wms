import React from 'react';
import assistantAvatar from '../../assets/assistant-avatar.png';
import { ASSISTANT_NAME } from '../../constants/branding';

interface AssistantAvatarProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const sizeClasses: Record<NonNullable<AssistantAvatarProps['size']>, string> = {
  sm: 'h-14 w-14 rounded-[22px] p-1.5',
  md: 'h-20 w-20 rounded-[28px] p-2',
  lg: 'h-32 w-32 rounded-[34px] p-2.5',
  xl: 'h-44 w-44 rounded-[42px] p-3',
};

export default function AssistantAvatar({
  size = 'md',
  className = '',
}: AssistantAvatarProps) {
  return (
    <div
      className={`ops-avatar-shell relative overflow-hidden ${sizeClasses[size]} ${className}`}
    >
      <div className="pointer-events-none absolute inset-x-5 top-1 h-10 rounded-full bg-[rgba(121,191,100,0.3)] blur-2xl" />
      <img
        src={assistantAvatar}
        alt={`${ASSISTANT_NAME} avatar`}
        className="relative h-full w-full rounded-[inherit] object-cover object-top"
      />
    </div>
  );
}
