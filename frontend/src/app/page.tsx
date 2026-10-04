import Link from 'next/link';
import { BackendStatus } from '@/components/backend-status';
import { FadeIn } from '@/components/fade-in';
import { buttonClasses } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const features = [
  {
    title: 'Structured lessons',
    description: 'Short, focused sessions that build from where you are.',
  },
  {
    title: 'Vocabulary that sticks',
    description: 'Spaced repetition keeps new words in long-term memory.',
  },
  {
    title: 'An AI tutor',
    description: 'Explanations, corrections and practice that adapt to you.',
  },
];

export default function HomePage() {
  return (
    <div className="space-y-14">
      <FadeIn>
        <section className="pt-8 text-center sm:pt-16">
          <span className="inline-flex items-center rounded-full border border-violet-500/30 bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-400">
            Premium English practice
          </span>
          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-bold tracking-tight text-slate-100 sm:text-6xl">
            Learn English with focus and momentum.
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base text-slate-400 sm:text-lg">
            Daily lessons, vocabulary review and an AI tutor in one calm, focused place. Start small,
            build a streak, and see real progress.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/learn" className={buttonClasses('primary', 'lg')}>
              Start Learning
            </Link>
            <Link href="/login" className={buttonClasses('secondary', 'lg')}>
              Log in
            </Link>
          </div>
        </section>
      </FadeIn>

      <section className="grid gap-4 sm:grid-cols-3">
        {features.map((feature, index) => (
          <FadeIn key={feature.title} delay={0.05 * (index + 1)}>
            <Card className="h-full">
              <h2 className="text-base font-semibold text-slate-100">{feature.title}</h2>
              <p className="mt-2 text-sm text-slate-400">{feature.description}</p>
            </Card>
          </FadeIn>
        ))}
      </section>

      <FadeIn delay={0.2}>
        <section className="mx-auto max-w-md">
          <Card>
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-sm font-medium text-slate-300">Backend status</h2>
                <p className="mt-1 text-xs text-slate-400">Live from GET /api/v1/health</p>
              </div>
              <BackendStatus />
            </div>
          </Card>
        </section>
      </FadeIn>
    </div>
  );
}
