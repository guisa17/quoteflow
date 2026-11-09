import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router'
import { Toaster } from 'sonner'
import { applyStoredTheme } from '@/lib/theme'
import { router } from '@/router'
import '@/index.css'

applyStoredTheme()

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('No se encontró el elemento #root en index.html.')
}

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster
        position="bottom-right"
        closeButton
        toastOptions={{
          classNames: {
            toast: '!bg-paper !text-ink !border-rule-strong !rounded-md !font-sans',
            description: '!text-ink-soft',
            error: '!border-stamp-red',
          },
        }}
      />
    </QueryClientProvider>
  </StrictMode>,
)
