import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import {
  armFailNextSignIn,
  armFailNextSignUp,
  armSignUpWithoutSession,
  resetAuthHarness,
} from './services/authApi.js'
import {
  armFailNextMeFetch,
  resetMeHarness,
  setMockMeRole,
} from './services/meApi.js'
import {
  armEmptyCurrentIssue,
  armFailNextContentFetch,
  clearFailNextContentFetch,
  resetContentHarness,
} from './services/contentApi.js'
import {
  armAlreadySentOnSend,
  armFailNextDecision,
  armFailNextPreview,
  armFailNextSend,
  armFailNextShortlistFetch,
  clearFailNextPreview,
  clearFailNextShortlistFetch,
  resetAdminHarness,
  getMockMarkReadyBatchCalls,
} from './services/adminApi.js'
import {
  armFailNextLoad,
  armFailNextSave,
  armRejectNextSave,
  resetPipelineConfigHarness,
} from './services/pipelineConfigApi.js'
import {
  armFailNextAdd,
  armFailNextDelete,
  armFailNextLoad as armFailNextIngestSourcesLoad,
  armFailNextSetEnabled,
  armRejectNextAdd,
  resetIngestSourcesHarness,
  resetIngestSourcesMockStore,
} from './services/ingestSourcesApi.js'
import {
  armFailNextScheduleLoad,
  armFailNextScheduleSave,
  readIngestionScheduleMock,
  resetIngestionScheduleHarness,
  resetIngestionScheduleMockStore,
} from './services/ingestScheduleApi.js'

// Playwright harness (mirrors votingApi arm-fail pattern).
window.__DIGEST_AUTH_HARNESS__ = {
  armFailNextSignIn,
  armFailNextSignUp,
  armSignUpWithoutSession,
  resetAuthHarness,
}
window.__DIGEST_ME_HARNESS__ = { armFailNextMeFetch, resetMeHarness, setMockMeRole }
window.__DIGEST_CONTENT_HARNESS__ = {
  armEmptyCurrentIssue,
  armFailNextContentFetch,
  clearFailNextContentFetch,
  resetContentHarness,
}
window.__DIGEST_ADMIN_HARNESS__ = {
  armFailNextShortlistFetch,
  clearFailNextShortlistFetch,
  armFailNextDecision,
  armFailNextPreview,
  clearFailNextPreview,
  armFailNextSend,
  armAlreadySentOnSend,
  resetAdminHarness,
  getMockMarkReadyBatchCalls,
}
window.__DIGEST_PIPELINE_CONFIG_HARNESS__ = {
  armFailNextLoad,
  armRejectNextSave,
  armFailNextSave,
  resetPipelineConfigHarness,
}
window.__DIGEST_INGEST_SOURCES_HARNESS__ = {
  armFailNextLoad: armFailNextIngestSourcesLoad,
  armFailNextAdd,
  armFailNextSetEnabled,
  armFailNextDelete,
  armRejectNextAdd,
  resetIngestSourcesHarness,
  resetIngestSourcesMockStore,
}
window.__DIGEST_INGESTION_SCHEDULE_HARNESS__ = {
  armFailNextLoad: armFailNextScheduleLoad,
  armFailNextSave: armFailNextScheduleSave,
  resetIngestionScheduleHarness,
  resetIngestionScheduleMockStore,
  readIngestionScheduleMock,
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
