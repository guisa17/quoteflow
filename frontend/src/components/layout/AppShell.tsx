import { Monitor, Moon, Plus, Sun } from 'lucide-react'
import { NavLink, Outlet } from 'react-router'

import { API_MODE } from '@/lib/config'
import { useTheme } from '@/lib/theme'
import { cn } from '@/lib/utils'

const THEME_META = {
  system: { icon: Monitor, label: 'Tema: sistema' },
  light: { icon: Sun, label: 'Tema: claro' },
  dark: { icon: Moon, label: 'Tema: oscuro' },
} as const

function navClass({ isActive }: { isActive: boolean }) {
  return cn(
    'relative flex h-12 items-center px-3 text-sm font-medium transition-colors',
    'after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:transition-colors',
    isActive
      ? 'text-bar-ink after:bg-bar-ink'
      : 'text-bar-ink-soft hover:text-bar-ink after:bg-transparent',
  )
}

/** Barra de tinta azul con la marca, la navegación y el tema. Debajo, el
 * escritorio sobre el que se apoyan los folios. */
export function AppShell() {
  const { choice, cycle } = useTheme()
  const ThemeIcon = THEME_META[choice].icon

  return (
    <div className="bg-desk text-ink flex min-h-dvh flex-col">
      <header className="bg-bar text-bar-ink sticky top-0 z-30">
        <div className="mx-auto flex h-12 max-w-[88rem] items-center gap-2 px-4 sm:px-6">
          <NavLink to="/" className="mr-3 flex items-center gap-2" aria-label="QuoteFlow, ir a la bandeja">
            <span
              aria-hidden
              className="border-bar-ink/70 font-code flex h-6 items-center rounded-[3px] border-[1.5px] px-1 text-[0.6875rem] font-semibold tracking-tight outline outline-1 outline-offset-[1.5px] outline-bar-ink/35"
            >
              QF
            </span>
            <span className="text-[0.9375rem] font-semibold tracking-[-0.01em]">QuoteFlow</span>
          </NavLink>

          <nav aria-label="Navegación principal" className="flex items-center">
            <NavLink to="/" end className={navClass}>
              Bandeja
            </NavLink>
          </nav>

          <div className="ml-auto flex items-center gap-1.5">
            {API_MODE === 'mock' && (
              <span className="text-bar-ink-soft hidden text-xs md:inline">
                Demo con datos ficticios · Ferrocima Industrial
              </span>
            )}
            <button
              type="button"
              onClick={cycle}
              aria-label={`${THEME_META[choice].label}. Cambiar tema`}
              title={THEME_META[choice].label}
              className="text-bar-ink-soft hover:text-bar-ink hover:bg-bar-ink/10 flex size-8 items-center justify-center rounded-md transition-colors"
            >
              <ThemeIcon aria-hidden className="size-4" />
            </button>
            <NavLink
              to="/new"
              className="bg-bar-ink text-bar hover:bg-bar-ink/90 inline-flex h-8 items-center gap-1.5 rounded-md px-3 text-sm font-semibold transition-colors"
            >
              <Plus aria-hidden className="size-4 stroke-[2.5]" />
              <span className="sm:hidden">Nueva</span>
              <span className="hidden sm:inline">Registrar solicitud</span>
            </NavLink>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
