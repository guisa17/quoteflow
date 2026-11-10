import { createBrowserRouter } from 'react-router'

import { AppShell } from '@/components/layout/AppShell'
import { InboxPage } from '@/features/inbox/InboxPage'
import { NewRequestPage } from '@/features/new-request/NewRequestPage'
import { NotFoundPage, RouteErrorPage } from '@/features/not-found/NotFoundPage'
import { RequestDetailPage } from '@/features/request-detail/RequestDetailPage'

export const router = createBrowserRouter([
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
])
