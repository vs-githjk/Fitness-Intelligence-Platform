export function titleize(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function formatDate(value: string | Date, options?: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat(undefined, options ?? { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value))
}

export function formatDateTime(value: string | Date): string {
  return new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }).format(new Date(value))
}

export function formatGoal(value?: string | null): string {
  return value ? titleize(value) : 'Not set'
}

export function severityRank(severity: string): number {
  return { urgent: 4, elevated: 3, review: 2, informational: 1 }[severity] ?? 0
}
