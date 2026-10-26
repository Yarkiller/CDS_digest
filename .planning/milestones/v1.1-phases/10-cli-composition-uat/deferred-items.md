# Deferred items — Phase 10 Plan 01

- `tests/unit/test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` — pre-existing failure (`sent_at` / `week_label` extras in response); out of scope for 10-01 PersistResult/CLI work.
- Live `SupabaseDraftPersister` `_RESULT_KEYS` / RPC `already_saved` parse — owned by 10-05 per plan.
  status: acknowledged
