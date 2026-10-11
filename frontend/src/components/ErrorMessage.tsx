interface ErrorMessageProps {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorMessage({
  title = 'Unable to load data',
  message,
  onRetry,
  className = '',
}: ErrorMessageProps) {
  return (
    <div
      role="alert"
      className={`border border-accent bg-surface p-6 space-y-4 text-left ${className}`}
    >
      <div className="space-y-1">
        <span className="font-mono text-small text-accent font-semibold block uppercase">
          {title}
        </span>
        <p className="text-body text-text m-0">
          {message}
        </p>
      </div>

      {onRetry && (
        <div>
          <button
            type="button"
            onClick={onRetry}
            className="bg-accent text-white px-5 py-3 min-h-[44px] hover:bg-accent-hover font-sans text-small border-0 cursor-pointer inline-flex items-center justify-center transition-colors"
          >
            Retry
          </button>
        </div>
      )}
    </div>
  )
}
