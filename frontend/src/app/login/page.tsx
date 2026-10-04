'use client';

import { useState, type FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // Authentication is not implemented yet. This deliberately does not fake a
    // session: see plans/backend-plan.md phase 2.
    setSubmitted(true);
  }

  return (
    <div className="mx-auto max-w-md pt-8">
      <header className="mb-6 text-center">
        <h1 className="text-2xl font-bold tracking-tight">Welcome back</h1>
        <p className="mt-2 text-sm text-slate-400">Log in to continue your learning.</p>
      </header>

      <Card>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-300">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-1.5 w-full rounded-xl border border-ink-600 bg-ink-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-400 focus:border-violet-500 focus:outline-none"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-300">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1.5 w-full rounded-xl border border-ink-600 bg-ink-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-400 focus:border-violet-500 focus:outline-none"
              placeholder="••••••••"
            />
          </div>

          <Button type="submit" className="w-full">
            Log in
          </Button>
        </form>

        {submitted && (
          <p
            role="status"
            className="mt-4 rounded-xl border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning"
          >
            Authentication is not implemented yet. This form is a UI scaffold and no session was
            created.
          </p>
        )}
      </Card>

      <p className="mt-4 text-center text-xs text-slate-400">
        Registration and password reset arrive with the auth milestone.
      </p>
    </div>
  );
}
