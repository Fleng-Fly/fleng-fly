'use client';

import { motion, useReducedMotion } from 'framer-motion';
import type { ReactNode } from 'react';

interface FadeInProps {
  children: ReactNode;
  className?: string;
  delay?: number;
}

/**
 * Small, purposeful entrance animation. Framer Motion is used only where it
 * adds clarity; users who prefer reduced motion get the static content.
 */
export function FadeIn({ children, className, delay = 0 }: FadeInProps) {
  const reduceMotion = useReducedMotion();

  if (reduceMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}
