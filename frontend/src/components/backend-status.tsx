'use client';

import { useQuery } from '@tanstack/react-query';
import { getHealth } from '@/lib/api/health';
import { Badge } from './ui/badge';

interface BackendStatusProps {
  compact?: boolean;
}

/**
 * Live backend status from GET /api/v1/health. Never hardcoded: when the API is
 * unreachable the badge switches to Offline.
 */
export function BackendStatus({ compact = false }: BackendStatusProps) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 15_000,
    retry: 1,
  });

  const state = isPending ? 'checking' : isError || !data ? 'offline' : 'online';

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-slate-400">Backend</span>
      {state === 'checking' && <Badge tone="neutral">Checking…</Badge>}
      {state === 'online' && <Badge tone="success">● Online</Badge>}
      {state === 'offline' && <Badge tone="danger">● Offline</Badge>}
      {!compact && state === 'online' && data && (
        <span className="text-slate-400">db {data.database}</span>
      )}
    </div>
  );
}
