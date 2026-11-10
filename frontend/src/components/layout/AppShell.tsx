import { Moon, Plus, Sun } from 'lucide-react'
import { NavLink, Outlet } from 'react-router'

import { API_MODE } from '@/lib/config'
import { useTheme, type Theme } from '@/lib/theme'
import { cn } from '@/lib/utils'

const THEMES: { value: Theme; icon: typeof Sun; label: string }[] = [
  { value: 'light', icon: Sun, label: 'Tema claro' },
  { value: 'dark', icon: Moon, label: 'Tema oscuro' },
]

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
  const { theme, setTheme } = useTheme()

  return (
    <div className="bg-desk text-ink flex min-h-dvh flex-col">
      <header className="bg-bar text-bar-ink sticky top-0 z-30">
        <div className="mx-auto flex h-12 max-w-[88rem] items-center gap-2 px-4 sm:px-6">
          <NavLink to="/" className="mr-3 flex items-center gap-2" aria-label="QuoteFlow, ir a la bandeja">
            <span
              aria-hidden
              className="border-bar-ink/70 font-code flex h-6 items-center rounded-[5px] border-[1.5px] px-1 text-[0.6875rem] font-semibold tracking-tight outline outline-1 outline-offset-[1.5px] outline-bar-ink/35"
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
            <div
              role="group"
              aria-label="Tema"
              className="bg-bar-ink/10 flex h-8 items-center gap-0.5 rounded-full p-0.5"
            >
              {THEMES.map(({ value, icon: Icon, label }) => {
                const active = theme === value
                return (
                  <button
                    key={value}
                    type="button"
                    aria-pressed={active}
                    aria-label={label}
                    title={label}
                    onClick={() => setTheme(value)}
                    className={cn(
                      'flex size-7 items-center justify-center rounded-full transition-colors',
                      active ? 'bg-bar-ink text-bar' : 'text-bar-ink-soft hover:text-bar-ink',
                    )}
                  >
                    <Icon aria-hidden className="size-3.5 stroke-[2.25]" />
                  </button>
                )
              })}
            </div>
            <NavLink
              to="/new"
              className="bg-bar-ink text-bar hover:bg-bar-ink/90 inline-flex h-8 items-center gap-1.5 rounded-full px-3.5 text-sm font-semibold transition-colors"
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
