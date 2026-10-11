import { createContext, useContext } from 'react'

export type RoutePath = '/' | '/map' | '/report' | '/method' | '/terms' | '/privacy'

export interface RouterContextType {
  path: string
  navigate: (to: string) => void
}

export const RouterContext = createContext<RouterContextType>({
  path: '/',
  navigate: () => {},
})

export function normalizePath(path: string): string {
  const clean = path.split('?')[0].split('#')[0]
  if (clean.length > 1 && clean.endsWith('/')) {
    return clean.slice(0, -1)
  }
  return clean || '/'
}

export function useRouter(): RouterContextType {
  return useContext(RouterContext)
}
