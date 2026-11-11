import { createBrowserRouter } from 'react-router'

import { AppShell } from '@/components/layout/AppShell'
import { InboxPage } from '@/features/inbox/InboxPage'
import { NewRequestPage } from '@/features/new-request/NewRequestPage'
import { NotFoundPage, RouteErrorPage } from '@/features/not-found/NotFoundPage'
import { RequestDetailPage } from '@/features/request-detail/RequestDetailPage'

// En GitHub Pages la app vive bajo /quoteflow/ (ver `base` en vite.config.ts).
const basename = import.meta.env.BASE_URL.replace(/\/$/, '') || '/'

export const router = createBrowserRouter(
  [
    {
      path: '/',
      element: <AppShell />,
      errorElement: <RouteErrorPage />,
      children: [
        { index: true, element: <InboxPage /> },
        { path: 'new', element: <NewRequestPage /> },
        { path: 'requests/:id', element: <RequestDetailPage /> },
        { path: '*', element: <NotFoundPage /> },
      ],
    },
  ],
  { basename },
)
