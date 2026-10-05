import Link from 'next/link';
import type { ReactNode } from 'react';
import { navItems } from '@/config/nav';
import { BackendStatus } from './backend-status';
import { UserMenu } from './user-menu';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 sm:px-6">
      <header className="sticky top-0 z-20 -mx-4 mb-8 border-b border-ink-700/60 bg-ink-950/70 px-4 backdrop-blur sm:-mx-6 sm:px-6">
        <div className="flex h-16 items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-violet-500 to-cyan-400 font-bold text-ink-950">
              F
            </span>
            <span className="text-lg font-semibold tracking-tight">Fleng</span>
          </Link>

          <nav className="flex items-center gap-1 text-sm">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-lg px-3 py-1.5 text-slate-300 transition-colors hover:bg-ink-800 hover:text-slate-100"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <div className="hidden sm:block">
              <BackendStatus compact />
            </div>
            <UserMenu />
          </div>
        </div>
      </header>

      <main className="flex-1 pb-16">{children}</main>

      <footer className="flex items-center justify-between gap-4 border-t border-ink-700/60 py-6 text-xs text-slate-400">
        <span>Fleng — learn English, every day.</span>
        <div className="sm:hidden">
          <BackendStatus compact />
        </div>
      </footer>
    </div>
  );
}
