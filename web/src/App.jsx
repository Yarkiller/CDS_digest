import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AnalyticsPageViews from './components/AnalyticsPageViews.jsx'
import AppShell from './components/AppShell.jsx'
import RequireAuth from './components/RequireAuth.jsx'
import ArchivePage from './pages/ArchivePage.jsx'
import IssuePage from './pages/IssuePage.jsx'
import KnowledgePage from './pages/KnowledgePage.jsx'
import LeaderboardPage from './pages/LeaderboardPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import MaterialPage from './pages/MaterialPage.jsx'
import AdminDigestPage from './pages/AdminDigestPage.jsx'
import AdminPipelineConfigPage from './pages/AdminPipelineConfigPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import RazborPage from './pages/RazborPage.jsx'
import RazboryListPage from './pages/RazboryListPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import VotingPage from './pages/VotingPage.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <AnalyticsPageViews />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route index element={<IssuePage isCurrent />} />
          <Route path="archive" element={<ArchivePage />} />
          <Route path="issues/:number" element={<IssuePage isCurrent={false} />} />
          <Route path="voting" element={<VotingPage />} />
          <Route path="knowledge" element={<KnowledgePage />} />
          <Route path="materials/:id" element={<MaterialPage />} />
          <Route path="razbory" element={<RazboryListPage />} />
          <Route path="razbory/:id" element={<RazborPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="leaderboard" element={<LeaderboardPage />} />
          <Route path="admin/digest" element={<AdminDigestPage />} />
          <Route path="admin/pipeline" element={<AdminPipelineConfigPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
