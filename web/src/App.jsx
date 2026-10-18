import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'
import AppShell from './components/AppShell.jsx'
import AdminLayout from './components/AdminLayout.jsx'
import RequireAuth from './components/RequireAuth.jsx'
import ArchivePage from './pages/ArchivePage.jsx'
import IssuePage from './pages/IssuePage.jsx'
import KnowledgePage from './pages/KnowledgePage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import MaterialPage from './pages/MaterialPage.jsx'
import AdminDigestPage from './pages/AdminDigestPage.jsx'
import AdminPipelineConfigPage from './pages/AdminPipelineConfigPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import RazborPage from './pages/RazborPage.jsx'
import RazboryListPage from './pages/RazboryListPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import VotingPage from './pages/VotingPage.jsx'

const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <IssuePage isCurrent /> },
      { path: 'archive', element: <ArchivePage /> },
      { path: 'issues/:number', element: <IssuePage isCurrent={false} /> },
      { path: 'voting', element: <VotingPage /> },
      { path: 'knowledge', element: <KnowledgePage /> },
      { path: 'materials/:id', element: <MaterialPage /> },
      { path: 'razbory', element: <RazboryListPage /> },
      { path: 'razbory/:id', element: <RazborPage /> },
      { path: 'profile', element: <ProfilePage /> },
      {
        // Pathless layout (D-01…D-04): shared admin chrome for digest + pipeline only.
        // No `/admin` index and no redirect — the shell «Админ» entry owns the URL.
        element: <AdminLayout />,
        children: [
          { path: 'admin/digest', element: <AdminDigestPage /> },
          { path: 'admin/pipeline', element: <AdminPipelineConfigPage /> },
        ],
      },
      // Sibling without the section switch (D-03, D-11).
      { path: 'admin/materials/:id', element: <MaterialPage preview /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
