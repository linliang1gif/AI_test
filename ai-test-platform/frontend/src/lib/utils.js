/**
 * Utility functions for shadcn/ui components.
 * Provides className merging via clsx + tailwind-merge pattern,
 * with a lightweight fallback when those packages are not installed.
 */

function cn(...inputs) {
  // Try to use clsx + tailwind-merge if available
  try {
    const clsx = require('clsx');
    const { twMerge } = require('tailwind-merge');
    return twMerge(clsx(inputs));
  } catch {
    // Lightweight fallback: filter falsy values and join
    return inputs
      .filter(Boolean)
      .flatMap(item => {
        if (typeof item === 'string') return item.split(/\s+/);
        if (Array.isArray(item)) return item;
        if (typeof item === 'object' && item !== null) {
          return Object.entries(item)
            .filter(([, value]) => value)
            .map(([key]) => key);
        }
        return [];
      })
      .filter((v, i, a) => a.indexOf(v) === i)
      .join(' ')
      .trim();
  }
}

export { cn };
export default cn;
