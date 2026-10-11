interface LoadingSkeletonProps {
  lines?: number
  className?: string
  height?: string
}

export function LoadingSkeleton({
  lines = 3,
  className = '',
  height = 'h-6',
}: LoadingSkeletonProps) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="Loading data"
      className={`border border-divider bg-surface p-4 space-y-3 ${className}`}
    >
      {Array.from({ length: lines }).map((_, idx) => (
        <div
          key={idx}
          className={`bg-bg border border-divider animate-pulse ${height} ${
            idx === lines - 1 ? 'w-3/5' : 'w-full'
          }`}
        />
      ))}
      <span className="sr-only">Loading content...</span>
    </div>
  )
}
