import { ChevronRight } from 'lucide-react'
import { Fragment, type ReactNode } from 'react'
import { Link } from 'react-router'

import { cn } from '@/lib/utils'

export interface Crumb {
  label: string
  to?: string
}

interface PageHeaderProps {
  title: string
  breadcrumbs?: Crumb[]
  actions?: ReactNode
  description?: string
}

/** Franja de vista fija: ruta + título a la izquierda, acciones a la
 * derecha. Vive en la parte superior de cada página, dentro de la misma
 * columna centrada que su contenido. */
export function PageHeader({ title, breadcrumbs, actions, description }: PageHeaderProps) {
  return (
    <header className="bg-background border-border sticky top-0 z-10 border-b">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
        <div className="min-w-0">
          {breadcrumbs && breadcrumbs.length > 0 && (
            <nav aria-label="Ruta de navegación" className="mb-0.5 flex items-center gap-1 text-xs">
              {breadcrumbs.map((crumb) => (
                <Fragment key={crumb.label}>
                  {crumb.to ? (
                    <Link
                      to={crumb.to}
                      className="text-muted-foreground hover:text-foreground truncate transition-colors"
                    >
                      {crumb.label}
                    </Link>
                  ) : (
                    <span className="text-muted-foreground truncate">{crumb.label}</span>
                  )}
                  <ChevronRight aria-hidden className="text-muted-foreground/50 size-3 shrink-0" />
                </Fragment>
              ))}
            </nav>
          )}
          <h1 className={cn('truncate text-base font-semibold')}>{title}</h1>
          {description && <p className="text-muted-foreground mt-0.5 text-xs">{description}</p>}
        </div>
        {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
      </div>
    </header>
  )
}

/** Columna centrada para el cuerpo de la página. */
export function PageBody({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn('mx-auto max-w-7xl space-y-5 px-4 py-5', className)}>{children}</div>
}
