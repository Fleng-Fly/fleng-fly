import type { ReactNode } from 'react';

export type BadgeTone = 'success' | 'danger' | 'neutral' | 'accent';

const tones: Record<BadgeTone, string> = {
  success: 'border-success/40 bg-success/10 text-success',
  danger: 'border-danger/40 bg-danger/10 text-danger',
  neutral: 'border-ink-600 bg-ink-800 text-slate-300',
  accent: 'border-violet-500/40 bg-violet-500/10 text-violet-400',
};

export function Badge({
  tone = 'neutral',
  children,
}: {
  tone?: BadgeTone;
  children: ReactNode;
}) {
  return (
    <span
      className={[
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        tones[tone],
      ].join(' ')}
    >
      {children}
    </span>
  );
}
