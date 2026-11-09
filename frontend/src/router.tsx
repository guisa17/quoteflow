import { createBrowserRouter } from 'react-router'

import { AppShell } from '@/components/layout/AppShell'
import { InboxPage } from '@/features/inbox/InboxPage'
import { NewRequestPage } from '@/features/new-request/NewRequestPage'
import { RequestDetailPage } from '@/features/request-detail/RequestDetailPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <InboxPage /> },
      { path: 'new', element: <NewRequestPage /> },
      { path: 'requests/:id', element: <RequestDetailPage /> },
    ],
  },
])
