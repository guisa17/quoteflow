import { useCallback, useEffect, useState } from 'react'

export type ThemeChoice = 'system' | 'light' | 'dark'
export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'quoteflow.theme'
const DARK_QUERY = '(prefers-color-scheme: dark)'

function readChoice(): ThemeChoice {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return value === 'light' || value === 'dark' ? value : 'system'
  } catch {
    return 'system'
  }
}

function systemTheme(): Theme {
  return typeof window !== 'undefined' && window.matchMedia?.(DARK_QUERY).matches ? 'dark' : 'light'
}

function apply(choice: ThemeChoice) {
  const root = document.documentElement
  if (choice === 'system') root.removeAttribute('data-theme')
  else root.setAttribute('data-theme', choice)
}

/** Se llama antes del primer render para que no haya parpadeo de tema. */
export function applyStoredTheme() {
  apply(readChoice())
}

/** Claro u oscuro con un clic. Mientras no se elija nada, sigue al sistema;
 * elegir el mismo tema que el sistema vuelve a seguirlo. */
export function useTheme() {
  const [choice, setChoice] = useState<ThemeChoice>(readChoice)
  const [system, setSystem] = useState<Theme>(systemTheme)

  useEffect(() => {
    const media = window.matchMedia?.(DARK_QUERY)
    if (!media) return
    const onChange = () => setSystem(media.matches ? 'dark' : 'light')
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [])

  useEffect(() => {
    apply(choice)
    try {
      if (choice === 'system') localStorage.removeItem(STORAGE_KEY)
      else localStorage.setItem(STORAGE_KEY, choice)
    } catch {
      // Sin almacenamiento: el tema elegido dura lo que la pestaña.
    }
  }, [choice])

  const setTheme = useCallback(
    (theme: Theme) => setChoice(theme === system ? 'system' : theme),
    [system],
  )

  const theme: Theme = choice === 'system' ? system : choice
  return { theme, setTheme }
}
