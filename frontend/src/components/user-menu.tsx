'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/auth-context';
import { buttonClasses } from './ui/button';

export function UserMenu() {
  const router = useRouter();
  const { user, isLoading, logout } = useAuth();

  if (isLoading) {
    return <span className="text-xs text-slate-400">…</span>;
  }

  if (user === null) {
    return (
      <Link href="/login" className={buttonClasses('ghost', 'sm')}>
        Log in
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="hidden text-sm text-slate-300 sm:inline">{user.displayName}</span>
      <button
        type="button"
        className={buttonClasses('ghost', 'sm')}
        onClick={async () => {
          await logout();
          router.push('/');
        }}
      >
        Log out
      </button>
    </div>
  );
}
