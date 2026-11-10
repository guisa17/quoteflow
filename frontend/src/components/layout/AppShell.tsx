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
    'relative flex h-14 items-center px-2 text-sm font-medium transition-colors sm:px-3',
    'after:absolute after:inset-x-2 sm:after:inset-x-3 after:bottom-0 after:h-0.5 after:transition-colors',
    isActive
      ? 'text-bar-ink after:bg-bar-ink'
      : 'text-bar-ink-soft hover:text-bar-ink after:bg-transparent',
  )
}

/** Encabezado blanco con la marca en serif, la navegación y el tema. Debajo,
 * el fondo sobre el que se apoyan las tarjetas. */
export function AppShell() {
  const { theme, setTheme } = useTheme()

  return (
    <div className="bg-desk text-ink flex min-h-dvh flex-col">
      <header className="bg-bar text-bar-ink border-rule sticky top-0 z-30 border-b">
        <div className="mx-auto flex h-14 max-w-[88rem] items-center gap-2 px-4 sm:px-6">
          <NavLink to="/" className="mr-1 flex items-baseline sm:mr-4" aria-label="QuoteFlow, ir a la bandeja">
            <span className="font-display text-[1.25rem] leading-none font-[560] tracking-[-0.02em] sm:text-[1.375rem]">
              QuoteFlow
            </span>
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
              className="border-rule-strong flex h-9 items-center gap-0.5 rounded-md border p-0.5"
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
                      'flex size-7 items-center justify-center rounded-[5px] transition-colors',
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
              className="bg-bar-ink text-bar hover:bg-bar-ink/85 inline-flex h-9 items-center gap-1.5 rounded-md px-3 text-sm font-medium transition-colors sm:px-4"
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
