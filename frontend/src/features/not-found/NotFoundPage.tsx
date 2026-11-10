import { Link, isRouteErrorResponse, useLocation, useRouteError } from 'react-router'

/** Ruta comodín dentro del AppShell: la cabecera y la navegación siguen
 * disponibles, así que el operador vuelve a la bandeja con un clic. */
export function NotFoundPage() {
  const { pathname } = useLocation()

  return (
    <div className="mx-auto max-w-xl px-4 py-20 text-center">
      <p className="field-label text-ink-soft">Error 404</p>
      <h1 className="type-title mt-2">Esta página no existe</h1>
      <p className="text-ink-soft mt-2 text-sm">
        No hay nada en <code className="font-mono">{pathname}</code>. Si llegaste desde un enlace a un folio,
        puede que la dirección esté incompleta.
      </p>
      <div className="mt-5 flex justify-center gap-2">
        <Link
          to="/"
          className="bg-ink text-paper inline-flex h-9 items-center rounded-md px-3 text-sm font-semibold"
        >
          Volver a la bandeja
        </Link>
        <Link
          to="/new"
          className="border-rule-strong hover:bg-paper inline-flex h-9 items-center rounded-md border px-3 text-sm font-semibold"
        >
          Registrar solicitud
        </Link>
      </div>
    </div>
  )
}

/** `errorElement` de la raíz: reemplaza la pantalla por defecto de react-router
 * si algo falla al renderizar. No depende del AppShell, porque el fallo
 * puede estar justamente ahí. */
export function RouteErrorPage() {
  const error = useRouteError()
  const detail = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : error instanceof Error
      ? error.message
      : 'Error desconocido.'

  return (
    <main className="bg-desk text-ink flex min-h-dvh items-center justify-center px-4">
      <div className="max-w-xl text-center">
        <p className="font-display text-2xl">QuoteFlow</p>
        <h1 className="mt-4 font-semibold">Algo salió mal al mostrar esta pantalla.</h1>
        <p className="text-ink-soft mt-1 text-sm">{detail}</p>
        <a
          href="/"
          className="bg-ink text-paper mt-5 inline-flex h-9 items-center rounded-md px-3 text-sm font-semibold"
        >
          Volver a la bandeja
        </a>
      </div>
    </main>
  )
}
