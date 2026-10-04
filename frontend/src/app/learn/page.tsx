'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { ApiError } from '@/lib/api/client';
import { getCurrentUser } from '@/lib/api/users';
import { Button, buttonClasses } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// Stand-in until the catalog/lessons API exists. Profile data below is real.
const PLACEHOLDER_LESSONS = [
  { id: 'l1', title: 'Everyday greetings', focus: 'Speaking · A1', minutes: 8, completed: true },
  { id: 'l2', title: 'Present simple', focus: 'Grammar · A1', minutes: 10, completed: true },
  { id: 'l3', title: 'At the café', focus: 'Listening · A2', minutes: 12, completed: false },
  { id: 'l4', title: 'Describing your day', focus: 'Writing · A2', minutes: 15, completed: false },
];

export default function LearnPage() {
  const profile = useQuery({ queryKey: ['currentUser'], queryFn: getCurrentUser });

  const completed = PLACEHOLDER_LESSONS.filter((lesson) => lesson.completed).length;
  const total = PLACEHOLDER_LESSONS.length;
  const percentage = total === 0 ? 0 : Math.round((completed / total) * 100);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Learn</h1>
        <p className="mt-2 text-sm text-slate-400">
          Your level, progress and next lessons in one place.
        </p>
      </header>

      {profile.isPending && (
        <Card aria-busy="true">
          <p className="text-sm text-slate-400">Loading your profile…</p>
        </Card>
      )}

      {profile.isError && (
        <Card className="border-danger/40">
          <h2 className="text-base font-semibold text-danger">Could not load your profile</h2>
          <p className="mt-2 text-sm text-slate-400">
            {profile.error instanceof ApiError && profile.error.status === 0
              ? 'The backend is unreachable. Make sure it is running on port 3001.'
              : profile.error instanceof Error
                ? profile.error.message
                : 'Unexpected error.'}
          </p>
          <Button variant="secondary" className="mt-4" onClick={() => profile.refetch()}>
            Try again
          </Button>
        </Card>
      )}

      {profile.data && (
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm text-slate-400">Signed in as</p>
              <p className="text-lg font-semibold text-slate-100">{profile.data.displayName}</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="rounded-xl border border-violet-500/40 bg-violet-500/10 px-4 py-2 text-center">
                <p className="text-xs text-violet-400">Level</p>
                <p className="text-xl font-bold text-slate-100">{profile.data.level}</p>
              </div>
              <div className="rounded-xl border border-ink-600 bg-ink-800/70 px-4 py-2 text-center">
                <p className="text-xs text-slate-400">XP</p>
                <p className="text-xl font-bold text-slate-100">{profile.data.xp}</p>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>
                {completed}/{total} lessons complete
              </span>
              <span>{percentage}%</span>
            </div>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-ink-700">
              <div
                className="h-full rounded-full bg-gradient-to-r from-violet-500 to-cyan-400 transition-all"
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        </Card>
      )}

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Lessons</h2>
          <span className="text-xs text-slate-400">Placeholder content until the catalog API lands</span>
        </div>
        <ul className="space-y-3">
          {PLACEHOLDER_LESSONS.map((lesson) => (
            <li key={lesson.id}>
              <Card className="flex items-center justify-between gap-4 p-4">
                <div>
                  <p className="font-medium text-slate-100">{lesson.title}</p>
                  <p className="mt-1 text-xs text-slate-400">
                    {lesson.focus} · {lesson.minutes} min
                  </p>
                </div>
                <span
                  className={
                    lesson.completed
                      ? 'text-xs font-medium text-success'
                      : 'text-xs font-medium text-slate-400'
                  }
                >
                  {lesson.completed ? 'Completed' : 'Not started'}
                </span>
              </Card>
            </li>
          ))}
        </ul>
      </section>

      <div className="flex flex-wrap items-center gap-3">
        <Button disabled title="The lesson player arrives in the next milestone">
          Continue learning
        </Button>
        <Link href="/" className={buttonClasses('ghost')}>
          Back home
        </Link>
      </div>
    </div>
  );
}
