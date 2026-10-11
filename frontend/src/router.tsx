import React, { useEffect, useState } from 'react'
import {
  normalizePath,
  RouterContext,
  useRouter,
} from './routerContext'
import type { RoutePath } from './routerContext'

export type { RoutePath }

export function RouterProvider({ children }: { children: React.ReactNode }) {
  const [path, setPath] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return normalizePath(window.location.pathname)
    }
    return '/'
  })

  useEffect(() => {
    const handlePopState = () => {
      setPath(normalizePath(window.location.pathname))
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const navigate = (to: string) => {
    const normalized = normalizePath(to)
    if (normalized !== path) {
      window.history.pushState({}, '', to)
      setPath(normalized)
      window.scrollTo(0, 0)
    }
  }

  return (
    <RouterContext.Provider value={{ path, navigate }}>
      {children}
    </RouterContext.Provider>
  )
}

interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string
  className?: string
  children: React.ReactNode
}

export function Link({ href, className, children, onClick, ...rest }: LinkProps) {
  const { navigate } = useRouter()

  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (onClick) {
      onClick(e)
    }

    // Allow standard behavior for external links, modified clicks, or default-prevented events
    if (
      e.defaultPrevented ||
      e.button !== 0 ||
      e.metaKey ||
      e.altKey ||
      e.ctrlKey ||
      e.shiftKey ||
      href.startsWith('http://') ||
      href.startsWith('https://') ||
      href.startsWith('mailto:') ||
      href.startsWith('#')
    ) {
      return
    }

    e.preventDefault()
    navigate(href)
  }

  return (
    <a href={href} className={className} onClick={handleClick} {...rest}>
      {children}
    </a>
  )
}
