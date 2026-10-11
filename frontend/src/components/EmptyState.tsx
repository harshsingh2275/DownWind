interface EmptyStateProps {
  title?: string
  message?: string
  className?: string
}

export function EmptyState({
  title = 'No active detections',
  message = 'No fire detections in this period for the selected region.',
  className = '',
}: EmptyStateProps) {
  return (
    <div
      role="status"
      className={`border border-divider bg-surface p-8 text-left space-y-2 ${className}`}
    >
      <span className="font-mono text-small text-text-muted font-medium block uppercase tracking-wide">
        {title}
      </span>
      <p className="text-body text-text m-0 max-w-[60ch]">
        {message}
      </p>
    </div>
  )
}
