'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { describeApiError } from '@/lib/api/errors';
import { getMyProgress } from '@/lib/api/progress';
import { useAuth } from '@/lib/auth/auth-context';
import { Button, buttonClasses } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-ink-600 bg-ink-800/70 px-4 py-3 text-center">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="mt-1 text-xl font-bold text-slate-100">{value}</p>
    </div>
  );
}

export default function LearnPage() {
  const router = useRouter();
  const { user, isLoading: sessionLoading } = useAuth();
  const progress = useQuery({
    queryKey: ['progress', 'me'],
    queryFn: getMyProgress,
    enabled: user !== null,
  });

  useEffect(() => {
    if (!sessionLoading && user === null) {
      router.replace('/login');
    }
  }, [sessionLoading, user, router]);

  if (sessionLoading || user === null) {
    return (
      <Card aria-busy="true">
        <p className="text-sm text-slate-400">Checking your session…</p>
      </Card>
    );
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Learn</h1>
        <p className="mt-2 text-sm text-slate-400">
          Your level, progress and next lessons in one place.
        </p>
      </header>

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-slate-400">Signed in as</p>
            <p className="text-lg font-semibold text-slate-100">{user.displayName}</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="rounded-xl border border-violet-500/40 bg-violet-500/10 px-4 py-2 text-center">
              <p className="text-xs text-violet-400">Level</p>
              <p className="text-xl font-bold text-slate-100">{user.level}</p>
            </div>
            <div className="rounded-xl border border-ink-600 bg-ink-800/70 px-4 py-2 text-center">
              <p className="text-xs text-slate-400">XP</p>
              <p className="text-xl font-bold text-slate-100">{user.xp}</p>
            </div>
          </div>
        </div>
      </Card>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Progress</h2>

        {progress.isPending && (
          <Card aria-busy="true">
            <p className="text-sm text-slate-400">Loading your progress…</p>
          </Card>
        )}

        {progress.isError && (
          <Card className="border-danger/40">
            <h3 className="text-base font-semibold text-danger">Could not load your progress</h3>
            <p className="mt-2 text-sm text-slate-400">{describeApiError(progress.error)}</p>
            <Button variant="secondary" className="mt-4" onClick={() => progress.refetch()}>
              Try again
            </Button>
          </Card>
        )}

        {progress.data && (
          <div className="grid gap-3 sm:grid-cols-3">
            <Stat label="Lessons completed" value={progress.data.lessonsCompleted} />
            <Stat label="Lessons started" value={progress.data.lessonsStarted} />
            <Stat label="Study minutes" value={progress.data.studyMinutes} />
          </div>
        )}
      </section>

      <Card>
        <h2 className="text-base font-semibold text-slate-100">Lessons are coming next</h2>
        <p className="mt-2 text-sm text-slate-400">
          The course catalog and lesson player arrive in the next milestone. Your account, profile
          and progress are already stored on the server.
        </p>
      </Card>

      <div className="flex flex-wrap items-center gap-3">
        <Link href="/" className={buttonClasses('ghost')}>
          Back home
        </Link>
      </div>
    </div>
  );
}
