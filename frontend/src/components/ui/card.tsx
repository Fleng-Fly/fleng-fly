import type { HTMLAttributes } from 'react';

export function Card({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={[
        'rounded-2xl border border-ink-700/70 bg-ink-850/80 p-6 backdrop-blur',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...props}
    />
  );
}
