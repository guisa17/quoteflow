import { Inbox, PlusCircle } from 'lucide-react'
import { NavLink, Outlet } from 'react-router'

import { cn } from '@/lib/utils'

function navLinkClass({ isActive }: { isActive: boolean }) {
  return cn(
    'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors',
    isActive
      ? 'bg-sidebar-accent text-sidebar-accent-foreground'
      : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground',
  )
}

/**
 * Barra superior delgada + panel de contenido, en vez del sidebar de app
 * multi-módulo de un producto más grande: QuoteFlow tiene tres destinos
 * (bandeja, nueva solicitud, detalle), no una familia de módulos que
 * justifique una barra lateral permanente (PROJECT.md §2.3, alcance
 * modesto). El panel flota sobre el canvas con hairline, mismo principio
 * de profundidad por borde que el resto de la app: nunca sombra.
 */
export function AppShell() {
  return (
    <div className="bg-canvas text-foreground flex h-screen flex-col overflow-hidden">
      <header className="border-sidebar-border bg-sidebar shrink-0 border-b">
        <div className="mx-auto flex h-12 max-w-7xl items-center gap-4 px-4">
          <NavLink to="/" className="flex items-center gap-2">
            <span
              aria-hidden
              className="bg-primary text-primary-foreground flex size-6 shrink-0 items-center justify-center rounded-md text-xs font-semibold"
            >
              Q
            </span>
            <span className="text-sidebar-foreground text-sm font-semibold tracking-tight">
              QuoteFlow
            </span>
          </NavLink>

          <nav aria-label="Navegación principal" className="flex items-center gap-1">
            <NavLink to="/" end className={navLinkClass}>
              <Inbox aria-hidden className="size-4 stroke-[1.5]" />
              Bandeja
            </NavLink>
          </nav>

          <div className="ml-auto">
            <NavLink
              to="/new"
              className="bg-primary text-primary-foreground hover:bg-primary-hover inline-flex h-8 items-center gap-1.5 rounded-md px-3 text-sm font-medium transition-colors"
            >
              <PlusCircle aria-hidden className="size-4" />
              Nueva solicitud
            </NavLink>
          </div>
        </div>
      </header>

      <main className="min-h-0 flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
