import type { ButtonHTMLAttributes } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost';
export type ButtonSize = 'sm' | 'md' | 'lg';

const base =
  'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50';

const variants: Record<ButtonVariant, string> = {
  primary:
    'bg-violet-500 text-white hover:bg-violet-400 active:bg-violet-600 shadow-lg shadow-violet-500/20',
  secondary: 'border border-ink-600 bg-ink-800/70 text-slate-100 hover:bg-ink-700',
  ghost: 'text-slate-300 hover:bg-ink-800 hover:text-slate-100',
};

const sizes: Record<ButtonSize, string> = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-6 text-base',
};

export function buttonClasses(
  variant: ButtonVariant = 'primary',
  size: ButtonSize = 'md',
  className = '',
): string {
  return [base, variants[variant], sizes[size], className].filter(Boolean).join(' ');
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function Button({ variant = 'primary', size = 'md', className, ...props }: ButtonProps) {
  return <button className={buttonClasses(variant, size, className)} {...props} />;
}
