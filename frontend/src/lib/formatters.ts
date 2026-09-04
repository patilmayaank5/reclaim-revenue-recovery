// Money & Operational Formatters

/**
 * Formats integer minor unit monetary value to display string.
 * Example: 499900 minor INR -> "â‚¹4,999.00"
 */
export function formatMoneyMinor(amountMinor: number | null | undefined, currency = 'INR'): string {
  if (amountMinor == null) return 'â€”';

  const major = amountMinor / 100;
  const symbolMap: Record<string, string> = {
    INR: 'â‚¹',
    USD: '$',
    EUR: 'â‚¬',
    GBP: 'Â£',
  };

  const symbol = symbolMap[currency.toUpperCase()] || `${currency} `;
  const formatted = new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(major);

  return `${symbol}${formatted}`;
}

/**
 * Formats Basis Points (BPS) to readable percentage string.
 * Example: 6500 BPS -> "65.0%"
 */
export function formatBps(bps: number | null | undefined): string {
  if (bps == null) return 'â€”';
  const pct = (bps / 100).toFixed(1);
  return `${pct}%`;
}

/**
 * Formats AI raw confidence (0.0 to 1.0) to readable string.
 * Example: 0.85 -> "85.0%"
 */
export function formatConfidence(conf: number | null | undefined): string {
  if (conf == null) return 'â€”';
  return `${(conf * 100).toFixed(1)}%`;
}

/**
 * Formats ISO date string to compact operational timestamp.
 */
export function formatTimestamp(isoStr: string | null | undefined): string {
  if (!isoStr) return 'â€”';
  try {
    const d = new Date(isoStr);
    return new Intl.DateTimeFormat('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(d);
  } catch {
    return isoStr;
  }
}
