import { useCallback, useEffect, useMemo, useState } from 'react'
import Markdown from 'react-markdown'
import { Link } from 'react-router-dom'
import rehypeSanitize from 'rehype-sanitize'
import rehypeSlug from 'rehype-slug'
import remarkGfm from 'remark-gfm'
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
import ForbiddenPage from './ForbiddenPage.jsx'
import { getAccessToken } from '../services/authApi.js'
import { MeApiError, fetchMe } from '../services/meApi.js'
import {
  AdminApiError,
  DIGEST_WEEKLY_CADENCE_DAYS,
  clearFailNextPreview,
  clearFailNextShortlistFetch,
  fetchShortlist,
  markReady,
  previewEmail,
  sendDigest,
  setDecision,
} from '../services/adminApi.js'
import { compositionFingerprint } from '../services/adminPreviewComposition.js'
import { preservePromotedReady } from '../services/adminReadyReconcile.js'

const TOAST_DISMISS_MS = 4000
const TOP_N = 3

let issueBlockSeq = 0
function nextIssueBlockId(prefix) {
  issueBlockSeq += 1
  return `${prefix}-${issueBlockSeq}`
}

/**
 * Sync material blocks to approved∩ready; preserve order + interstitial text.
 * @param {Array<{ id: string, kind: 'material', material_id: number } | { id: string, kind: 'text', text: string }>} prev
 * @param {Array<{ material_id: number, rank: number }>} approvedReady
 */
function syncIssueBlocks(prev, approvedReady) {
  const readyIds = new Set((approvedReady ?? []).map((item) => item.material_id))
  const kept = []
  const seen = new Set()
  for (const block of prev ?? []) {
    if (!block || typeof block !== 'object') continue
    if (block.kind === 'material') {
      if (readyIds.has(block.material_id) && !seen.has(block.material_id)) {
        kept.push(block)
        seen.add(block.material_id)
      }
      continue
    }
    if (block.kind === 'text') {
      kept.push(block)
    }
  }
  const missing = [...(approvedReady ?? [])]
    .sort((a, b) => a.rank - b.rank)
    .filter((item) => !seen.has(item.material_id))
  for (const item of missing) {
    kept.push({
      id: nextIssueBlockId(`m-${item.material_id}`),
      kind: 'material',
      material_id: item.material_id,
    })
  }
  return kept
}

function materialStatusLabel(status) {
  if (status === 'ready') return 'готов'
  if (status === 'draft') return 'черновик'
  return status
}

function decisionCaption(decision) {
  if (decision === 'approved') return 'одобрен (в шортлист)'
  if (decision === 'rejected') return 'отклонён (из шортлиста)'
  return null
}

function factorText(item) {
  const labels = Array.isArray(item.factor_labels) ? item.factor_labels.filter(Boolean) : []
  if (labels.length < 2) return 'Обоснование недоступно — скоринг не запускался'
  return labels.join(' · ')
}

function applyBatch(dto, setItems, setBatchMeta, setDigestRest, setDaysUntilNext) {
  setItems(Array.isArray(dto?.items) ? dto.items : [])
  setBatchMeta({
    batch_id: dto?.batch_id ?? null,
    sent_at: dto?.sent_at ?? null,
    week_label: dto?.week_label ?? null,
  })
  setDigestRest(Boolean(dto?.digest_rest))
  const days = dto?.days_until_next_batch
  setDaysUntilNext(
    days == null || Number.isNaN(Number(days)) ? DIGEST_WEEKLY_CADENCE_DAYS : Number(days),
  )
}

/**
 * Admin Digest triage + preview/send gate (ADMIN-01…08 / D-75…D-90).
 */
export default function AdminDigestPage() {
  const [roleState, setRoleState] = useState('loading')
  const [roleKey, setRoleKey] = useState(0)
  const [items, setItems] = useState([])
  const [batchMeta, setBatchMeta] = useState({
    batch_id: null,
    sent_at: null,
    week_label: null,
  })
  const [loadState, setLoadState] = useState('loading')
  const [loadKey, setLoadKey] = useState(0)
  const [checkedIds, setCheckedIds] = useState(() => new Set())
  const [mutating, setMutating] = useState(false)
  const [toast, setToast] = useState('')
  const [banner, setBanner] = useState('')
  const [issueUrl, setIssueUrl] = useState('')
  const [previewItem, setPreviewItem] = useState(null)
  const [emailModal, setEmailModal] = useState(null) // null | loading | error | { preview }
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [sending, setSending] = useState(false)
  const [previewing, setPreviewing] = useState(false)
  const [emailPreviewed, setEmailPreviewed] = useState(false)
  const [previewFingerprint, setPreviewFingerprint] = useState('')
  const [contextText, setContextText] = useState('')
  const [issueBlocks, setIssueBlocks] = useState([])
  const [batchSent, setBatchSent] = useState(false)
  const [digestRest, setDigestRest] = useState(false)
  const [daysUntilNextBatch, setDaysUntilNextBatch] = useState(DIGEST_WEEKLY_CADENCE_DAYS)

  useEffect(() => {
    let cancelled = false
    async function loadRole() {
      setRoleState('loading')
      try {
        const token = await getAccessToken()
        const me = await fetchMe(token)
        if (!cancelled) {
          setRoleState(me.role === 'admin' ? 'admin' : 'forbidden')
        }
      } catch (err) {
        if (cancelled) return
        // WR-03: only authz failures are Forbidden; network/5xx → error + retry
        if (
          err instanceof MeApiError &&
          (err.code === 'UNAUTHORIZED' || err.code === 'FORBIDDEN')
        ) {
          setRoleState('forbidden')
        } else {
          setRoleState('error')
        }
      }
    }
    loadRole()
    return () => {
      cancelled = true
    }
  }, [roleKey])

  const reloadRole = useCallback(() => {
    setRoleKey((k) => k + 1)
  }, [])

  const reloadShortlist = useCallback(() => {
    clearFailNextShortlistFetch()
    setLoadKey((k) => k + 1)
  }, [])

  useEffect(() => {
    if (roleState !== 'admin') return undefined
    let cancelled = false
    setLoadState('loading')
    fetchShortlist()
      .then((dto) => {
        if (cancelled) return
        applyBatch(dto, setItems, setBatchMeta, setDigestRest, setDaysUntilNextBatch)
        setCheckedIds(new Set())
        setEmailPreviewed(false)
        setPreviewFingerprint('')
        setBatchSent(Boolean(dto?.sent_at) || Boolean(dto?.digest_rest))
        setBanner('')
        setIssueUrl('')
        setLoadState('ready')
      })
      .catch(() => {
        if (cancelled) return
        setLoadState('error')
      })
    return () => {
      cancelled = true
    }
  }, [roleState, loadKey])

  useEffect(() => {
    if (!toast) return undefined
    const id = window.setTimeout(() => setToast(''), TOAST_DISMISS_MS)
    return () => window.clearTimeout(id)
  }, [toast])

  const fingerprint = useMemo(
    () =>
      compositionFingerprint({
        intro: contextText,
        blocks: issueBlocks.map((block) =>
          block.kind === 'material'
            ? { kind: 'material', material_id: block.material_id }
            : { kind: 'text', text: block.text ?? '' },
        ),
      }),
    [contextText, issueBlocks],
  )

  useEffect(() => {
    if (emailPreviewed && previewFingerprint && fingerprint !== previewFingerprint) {
      setEmailPreviewed(false)
      setPreviewFingerprint('')
    }
  }, [fingerprint, emailPreviewed, previewFingerprint])

  const approvedReady = useMemo(
    () => items.filter((item) => item.decision === 'approved' && item.material_status === 'ready'),
    [items],
  )
  const approvedDrafts = useMemo(
    () => items.filter((item) => item.decision === 'approved' && item.material_status === 'draft'),
    [items],
  )

  useEffect(() => {
    setIssueBlocks((prev) => syncIssueBlocks(prev, approvedReady))
  }, [approvedReady])

  const titleByMaterialId = useMemo(() => {
    const map = new Map()
    for (const item of items) {
      map.set(item.material_id, item.title)
    }
    return map
  }, [items])

  const previewOk =
    emailPreviewed && previewFingerprint === fingerprint && fingerprint.length > 0
  const sendUnlocked =
    approvedReady.length >= 1 &&
    approvedDrafts.length === 0 &&
    previewOk &&
    !batchSent &&
    !batchMeta.sent_at

  const sendHint = useMemo(() => {
    if (batchSent || batchMeta.sent_at) return 'Уже отправлено'
    if (approvedReady.length === 0) {
      return 'Нет одобренных ready-материалов для отправки.'
    }
    if (approvedDrafts.length > 0) return 'Отправка недоступна.'
    if (!previewOk) return 'Сначала откройте превью письма.'
    return 'Превью просмотрено. Можно отправить.'
  }, [approvedDrafts.length, approvedReady.length, batchMeta.sent_at, batchSent, previewOk])

  const checkedCount = checkedIds.size
  const approveDisabled = mutating || checkedCount === 0

  const weekDek = useMemo(() => {
    if (!batchMeta.week_label) return null
    return `Неделя ${batchMeta.week_label} · до 5 кандидатов`
  }, [batchMeta.week_label])

  function toggleCheck(materialId) {
    setCheckedIds((prev) => {
      const next = new Set(prev)
      if (next.has(materialId)) next.delete(materialId)
      else next.add(materialId)
      return next
    })
  }

  function selectAll() {
    setCheckedIds(new Set(items.map((item) => item.material_id)))
  }

  function selectTopN() {
    const top = [...items]
      .sort((a, b) => a.rank - b.rank)
      .slice(0, TOP_N)
      .map((item) => item.material_id)
    setCheckedIds(new Set(top))
  }

  async function applyDecision(decision) {
    if (approveDisabled) return
    const ids = [...checkedIds]
    setMutating(true)
    const failed = []
    let latest = null
    try {
      for (const id of ids) {
        try {
          latest = await setDecision(id, decision)
        } catch {
          failed.push(id)
        }
      }
      if (failed.length > 0) {
        // WR-06: reload honest shortlist; keep failed ids selected; toast which failed
        try {
          const dto = await fetchShortlist()
          applyBatch(dto, setItems, setBatchMeta, setDigestRest, setDaysUntilNextBatch)
        } catch {
          if (latest) {
            applyBatch(latest, setItems, setBatchMeta, setDigestRest, setDaysUntilNextBatch)
          }
        }
        setToast(
          failed.length === ids.length
            ? 'Не сохранено'
            : `Не сохранено: ${failed.join(', ')}`,
        )
        setCheckedIds(new Set(failed))
        return
      }
      if (latest) {
        applyBatch(latest, setItems, setBatchMeta, setDigestRest, setDaysUntilNextBatch)
      }
      setCheckedIds(new Set())
    } finally {
      setMutating(false)
    }
  }

  async function promoteReady(item) {
    if (!item || item.material_status !== 'draft' || mutating) return
    const emptyBody = !(item.body_markdown || '').trim()
    if (emptyBody) {
      const ok = window.confirm('Текст пуст. Сделать ready и продолжить?')
      if (!ok) return
    }
    setMutating(true)
    const previous = items
    setItems((prev) =>
      prev.map((row) =>
        row.material_id === item.material_id ? { ...row, material_status: 'ready' } : row,
      ),
    )
    try {
      await markReady(item.material_id)
      try {
        const refreshed = await fetchShortlist()
        applyBatch(
          {
            ...refreshed,
            items: preservePromotedReady(refreshed.items, [item.material_id]),
          },
          setItems,
          setBatchMeta,
          setDigestRest,
          setDaysUntilNextBatch,
        )
      } catch {
        // keep optimistic ready; silent refetch best-effort (G-14-2 / D-05)
      }
    } catch (err) {
      setItems(previous)
      setToast(err instanceof AdminApiError ? err.message : 'Не удалось сделать ready')
    } finally {
      setMutating(false)
    }
  }

  function moveIssueBlock(index, delta) {
    setIssueBlocks((prev) => {
      const nextIndex = index + delta
      if (nextIndex < 0 || nextIndex >= prev.length) return prev
      const next = [...prev]
      const [block] = next.splice(index, 1)
      next.splice(nextIndex, 0, block)
      return next
    })
  }

  function addTextBlock() {
    setIssueBlocks((prev) => [
      ...prev,
      { id: nextIssueBlockId('t'), kind: 'text', text: '' },
    ])
  }

  function updateTextBlock(id, text) {
    setIssueBlocks((prev) =>
      prev.map((block) => (block.id === id && block.kind === 'text' ? { ...block, text } : block)),
    )
  }

  function removeTextBlock(id) {
    setIssueBlocks((prev) => prev.filter((block) => !(block.kind === 'text' && block.id === id)))
  }

  async function openEmailPreview() {
    setPreviewing(true)
    setEmailModal('loading')
    setBanner('')
    try {
      const blocks = issueBlocks.map((block) =>
        block.kind === 'material'
          ? { kind: 'material', material_id: block.material_id }
          : { kind: 'text', text: block.text ?? '' },
      )
      const preview = await previewEmail(undefined, { intro: contextText, blocks })
      const fp = compositionFingerprint({ intro: contextText, blocks })
      setEmailPreviewed(true)
      setPreviewFingerprint(fp)
      // If the user closed while loading, do not reopen the modal (D-86 session flag still set).
      setEmailModal((current) => (current === null ? null : { preview }))
    } catch {
      setEmailPreviewed(false)
      setPreviewFingerprint('')
      setEmailModal((current) => (current === null ? null : 'error'))
    } finally {
      setPreviewing(false)
    }
  }

  async function confirmSend() {
    if (sending) return
    setSending(true)
    setBanner('')
    try {
      const materialIds = issueBlocks
        .filter((block) => block.kind === 'material')
        .map((block) => block.material_id)
      const blocks = issueBlocks.map((block) =>
        block.kind === 'material'
          ? { kind: 'material', material_id: block.material_id }
          : { kind: 'text', text: block.text ?? '' },
      )
      const result = await sendDigest(undefined, {
        material_ids: materialIds,
        intro: contextText,
        blocks,
      })
      setBanner(result.message || 'Отправка записана')
      setIssueUrl(typeof result.issue_url === 'string' ? result.issue_url : '')
      setBatchSent(true)
      setDigestRest(true)
      setDaysUntilNextBatch(DIGEST_WEEKLY_CADENCE_DAYS)
      setItems([])
      setCheckedIds(new Set())
      setConfirmOpen(false)
    } catch (err) {
      if (err instanceof AdminApiError && err.code === 'ALREADY_SENT') {
        setBanner('Уже отправлено')
        setIssueUrl('')
        setBatchSent(true)
        setDigestRest(true)
        setDaysUntilNextBatch(DIGEST_WEEKLY_CADENCE_DAYS)
        setItems([])
        setCheckedIds(new Set())
        setConfirmOpen(false)
      } else {
        setBanner('Рассылка не отправлена')
        setIssueUrl('')
        setConfirmOpen(false)
      }
    } finally {
      setSending(false)
    }
  }

  if (roleState === 'loading') {
    return (
      <section aria-busy="true" data-testid="admin-role-loading">
        <p className="text-sm text-muted">Загрузка…</p>
      </section>
    )
  }

  if (roleState === 'forbidden') {
    return <ForbiddenPage />
  }

  if (roleState === 'error') {
    return (
      <section data-testid="admin-digest-page">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>
        <h1 className="mt-2 font-sans text-3xl font-semibold text-ink">Shortlist дайджеста</h1>
        <ServiceUnavailable onRetry={reloadRole} />
      </section>
    )
  }

  if (loadState === 'error') {
    return (
      <section data-testid="admin-digest-page">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>
        <h1 className="mt-2 font-sans text-3xl font-semibold text-ink">Shortlist дайджеста</h1>
        <ServiceUnavailable onRetry={reloadShortlist} />
      </section>
    )
  }

  if (loadState === 'loading') {
    return (
      <section aria-busy="true" data-testid="admin-digest-page">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>
        <h1 className="mt-2 font-sans text-3xl font-semibold text-ink">Shortlist дайджеста</h1>
        <p className="mt-4 text-sm text-muted">Загрузка…</p>
      </section>
    )
  }

  const restMode = batchSent || digestRest
  const isEmpty = !restMode && items.length === 0
  const showTriage = !restMode && items.length > 0
  const restDays =
    daysUntilNextBatch == null ? DIGEST_WEEKLY_CADENCE_DAYS : daysUntilNextBatch

  return (
    <section data-testid="admin-digest-page" className="pb-32">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>
      <h1 className="mt-2 font-sans text-3xl font-semibold text-ink">Shortlist дайджеста</h1>
      {showTriage && weekDek ? (
        <p className="mt-2 text-xs text-muted">{weekDek}</p>
      ) : null}

      {restMode ? (
        <div
          data-testid="admin-digest-rest"
          className="mt-8 rounded-2xl border border-rule bg-paper px-6 py-10"
        >
          <h2 className="font-sans text-3xl font-semibold text-ink">дайджест успешно выпущен</h2>
          <p className="mt-3 text-sm text-ink-2">
            Следующие материалы будут подготовлены через {restDays} дней
          </p>
        </div>
      ) : null}

      {isEmpty ? (
        <div
          data-testid="admin-shortlist-empty"
          className="mt-8 rounded-2xl border border-rule bg-paper px-6 py-10"
        >
          <h2 className="font-sans text-3xl font-semibold text-ink">Кандидатов пока нет</h2>
          <p className="mt-3 text-sm text-ink-2">Обновите список позже.</p>
          <button
            type="button"
            className="mt-6 inline-flex min-h-11 items-center font-medium text-accent hover:underline"
            onClick={reloadShortlist}
          >
            Обновить список
          </button>
        </div>
      ) : null}

      {showTriage ? (
        <>
          <div className="mt-6 flex flex-wrap gap-2">
            <button
              type="button"
              className="inline-flex min-h-11 items-center rounded-full border border-rule px-4 text-sm font-medium text-ink hover:bg-paper-2"
              onClick={selectAll}
            >
              Выбрать все
            </button>
            <button
              type="button"
              className="inline-flex min-h-11 items-center rounded-full border border-rule px-4 text-sm font-medium text-ink hover:bg-paper-2"
              onClick={selectTopN}
            >
              Оставить топ-3
            </button>
            <button
              type="button"
              disabled={approveDisabled}
              className="inline-flex min-h-11 items-center rounded-full border border-rule px-4 text-sm font-medium text-ink disabled:cursor-not-allowed disabled:opacity-45"
              onClick={() => applyDecision('approved')}
            >
              Одобрить выбранные
            </button>
            <button
              type="button"
              disabled={approveDisabled}
              className="inline-flex min-h-11 items-center rounded-full border border-rule px-4 text-sm font-medium text-ink disabled:cursor-not-allowed disabled:opacity-45"
              onClick={() => applyDecision('rejected')}
            >
              Отклонить выбранные
            </button>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            <section className="rounded-2xl border border-rule bg-paper-2/40 p-5">
              <h2 className="text-2xl font-semibold text-ink">Контекст дайджеста</h2>
              <label className="mt-4 block text-sm">
                <span className="font-medium text-ink-2">Вводный текст</span>
                <textarea
                  className="mt-2 min-h-28 w-full rounded-xl border border-rule bg-paper p-3 text-sm"
                  value={contextText}
                  onChange={(e) => setContextText(e.target.value)}
                  rows={5}
                />
                <span className="mt-1 block text-xs text-muted">Пустая строка = новый абзац</span>
              </label>
            </section>
            <section className="rounded-2xl border border-rule bg-paper-2/40 p-5">
              <h2 className="text-2xl font-semibold text-ink">Схема дайджеста</h2>
              <div className="mt-4">
                <span className="block text-sm font-medium text-ink-2">Блоки выпуска</span>
                <ul
                  data-testid="admin-issue-blocks"
                  className="mt-2 space-y-2"
                  aria-label="Блоки выпуска"
                >
                  {issueBlocks.length === 0 ? (
                    <li className="rounded-xl border border-dashed border-rule bg-paper p-3 text-sm text-muted">
                      Одобрите ready-материалы — они появятся здесь как блоки выпуска.
                    </li>
                  ) : null}
                  {issueBlocks.map((block, index) => {
                    const isMaterial = block.kind === 'material'
                    return (
                      <li
                        key={block.id}
                        data-testid={
                          isMaterial ? 'admin-issue-block-material' : 'admin-issue-block-text'
                        }
                        className="flex flex-col gap-2 rounded-xl border border-rule bg-paper p-3 sm:flex-row sm:items-start"
                      >
                        <div className="min-w-0 flex-1">
                          {isMaterial ? (
                            <p className="break-words text-sm font-medium text-ink">
                              {titleByMaterialId.get(block.material_id) ??
                                `Материал ${block.material_id}`}
                            </p>
                          ) : (
                            <label className="block text-sm">
                              <span className="sr-only">Связующий текст</span>
                              <textarea
                                className="min-h-20 w-full rounded-lg border border-rule bg-paper p-2 text-sm"
                                value={block.text}
                                onChange={(e) => updateTextBlock(block.id, e.target.value)}
                                rows={3}
                                placeholder="Необязательный связующий текст"
                              />
                              <span className="mt-1 block text-xs text-muted">
                                Пустая строка = новый абзац
                              </span>
                            </label>
                          )}
                        </div>
                        <div className="flex shrink-0 flex-wrap gap-1">
                          <button
                            type="button"
                            className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-full border border-rule text-sm disabled:cursor-not-allowed disabled:opacity-45"
                            aria-label="Переместить вверх"
                            disabled={index === 0}
                            onClick={() => moveIssueBlock(index, -1)}
                          >
                            ↑
                          </button>
                          <button
                            type="button"
                            className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-full border border-rule text-sm disabled:cursor-not-allowed disabled:opacity-45"
                            aria-label="Переместить вниз"
                            disabled={index === issueBlocks.length - 1}
                            onClick={() => moveIssueBlock(index, 1)}
                          >
                            ↓
                          </button>
                          {!isMaterial ? (
                            <button
                              type="button"
                              className="inline-flex min-h-11 items-center rounded-full border border-rule px-3 text-sm"
                              onClick={() => removeTextBlock(block.id)}
                            >
                              Удалить
                            </button>
                          ) : null}
                        </div>
                      </li>
                    )
                  })}
                </ul>
                <button
                  type="button"
                  className="mt-3 inline-flex min-h-11 items-center rounded-full border border-rule px-4 text-sm font-medium text-ink"
                  onClick={addTextBlock}
                >
                  Добавить текст
                </button>
              </div>
            </section>
          </div>

          <ul className="mt-8 space-y-3" data-testid="admin-shortlist">
            {items.map((item) => {
              const caption = decisionCaption(item.decision)
              const excluded = item.decision === 'rejected'
              return (
                <li
                  key={item.material_id}
                  data-testid="admin-shortlist-row"
                  className={[
                    'grid grid-cols-[auto_auto_1fr_auto] items-start gap-3 rounded-2xl border border-rule bg-paper p-4 sm:grid-cols-[auto_auto_1fr_auto_auto]',
                    excluded ? 'opacity-70' : '',
                  ].join(' ')}
                >
                  <label className="inline-flex min-h-11 min-w-11 items-center justify-center">
                    <input
                      type="checkbox"
                      checked={checkedIds.has(item.material_id)}
                      onChange={() => toggleCheck(item.material_id)}
                      aria-label={`Выбрать материал ${item.rank}`}
                    />
                  </label>
                  <span className="font-mono text-sm text-muted">{item.rank}</span>
                  <div className="min-w-0">
                    <p className="break-words font-medium text-ink">{item.title}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span
                        className={[
                          'rounded-md px-2 py-0.5 text-xs font-medium',
                          item.material_status === 'ready'
                            ? 'bg-[oklch(92%_0.04_155)] text-[oklch(35%_0.1_155)]'
                            : 'bg-[oklch(93%_0.05_50)] text-[oklch(45%_0.12_38)]',
                        ].join(' ')}
                      >
                        {materialStatusLabel(item.material_status)}
                      </span>
                      {item.material_status === 'draft' ? (
                        <button
                          type="button"
                          data-testid="admin-mark-ready"
                          className="inline-flex min-h-11 items-center text-sm text-accent hover:underline disabled:opacity-50"
                          disabled={mutating}
                          onClick={() => promoteReady(item)}
                        >
                          Сделать ready
                        </button>
                      ) : null}
                      {caption ? <span className="text-xs text-muted">{caption}</span> : null}
                    </div>
                  </div>
                  <div className="text-right">
                    {item.score != null ? (
                      <p className="font-mono text-sm text-ink">{item.score}</p>
                    ) : null}
                    <p className="mt-1 max-w-[12rem] break-words text-xs text-muted">
                      {factorText(item)}
                    </p>
                  </div>
                  <button
                    type="button"
                    className="col-span-full inline-flex min-h-11 items-center justify-self-start rounded-full px-3 text-sm text-accent hover:underline sm:col-span-1 sm:justify-self-end"
                    onClick={() => setPreviewItem(item)}
                  >
                    Превью материала
                  </button>
                </li>
              )
            })}
          </ul>
        </>
      ) : null}

      {showTriage || restMode ? (
        <div
          data-testid="admin-send-footer"
          className="fixed inset-x-0 bottom-0 z-40 border-t border-rule bg-paper/95 backdrop-blur"
        >
          <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="text-sm text-ink-2 break-words" data-testid="admin-send-hint">
                {sendHint}
              </p>
              {banner ? (
                <p className="mt-1 text-sm font-medium text-[oklch(45%_0.13_155)]" role="status">
                  <span>{banner}</span>
                  {issueUrl ? (
                    <>
                      {' · '}
                      <Link to={issueUrl} className="text-accent underline-offset-2 hover:underline">
                        К выпуску →
                      </Link>
                    </>
                  ) : null}
                </p>
              ) : null}
            </div>
            <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
              <button
                type="button"
                className="inline-flex min-h-11 w-full items-center justify-center rounded-full border border-rule px-4 text-sm font-medium sm:w-auto"
                disabled={restMode || previewing || approvedReady.length === 0}
                onClick={openEmailPreview}
              >
                Предпросмотр письма
              </button>
              <button
                type="button"
                className="inline-flex min-h-11 w-full items-center justify-center rounded-full bg-[oklch(45%_0.13_155)] px-4 text-sm font-medium text-paper disabled:cursor-not-allowed disabled:opacity-45 sm:w-auto"
                disabled={restMode || !sendUnlocked || sending}
                onClick={() => setConfirmOpen(true)}
              >
                Отправить дайджест →
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {toast ? (
        <p
          data-testid="admin-toast"
          className="fixed bottom-24 left-1/2 z-50 -translate-x-1/2 rounded-full bg-ink px-4 py-2 text-sm text-paper"
          role="status"
        >
          {toast}
        </p>
      ) : null}

      {previewItem ? (
        <AdminItemPreview item={previewItem} onClose={() => setPreviewItem(null)} />
      ) : null}

      {emailModal ? (
        <div
          className="fixed inset-0 z-[400] flex items-center justify-center bg-ink/40 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="email-preview-title"
        >
          <div className="flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl bg-paper">
            <div className="flex shrink-0 items-start justify-between gap-3 px-6 pt-6">
              <h2 id="email-preview-title" className="text-2xl font-semibold">
                Превью письма
              </h2>
              <button
                type="button"
                className="inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center"
                aria-label="Закрыть"
                onClick={() => setEmailModal(null)}
              >
                ✕
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto px-6 pb-6">
              {emailModal === 'loading' ? (
                <p className="mt-4 text-sm text-muted">Загрузка…</p>
              ) : emailModal === 'error' ? (
                <div className="mt-4">
                  <p className="text-sm text-ink-2">Превью недоступно</p>
                  <button
                    type="button"
                    className="mt-4 inline-flex min-h-11 items-center font-medium text-accent hover:underline"
                    onClick={() => {
                      clearFailNextPreview()
                      openEmailPreview()
                    }}
                  >
                    Повторить превью
                  </button>
                </div>
              ) : (
                <>
                  <p className="mt-2 text-xs text-muted">только одобренные ready</p>
                  <p className="mt-3 font-display text-xl font-semibold break-words">
                    {emailModal.preview.subject}
                  </p>
                  {emailModal.preview.html ? (
                    // D-11/T-18-05: popups must escape the frame so the CTA is not inert;
                    // script and same-origin powers stay deliberately OFF.
                    <iframe
                      data-testid="email-preview-frame"
                      title="Превью письма HTML"
                      sandbox="allow-popups allow-popups-to-escape-sandbox"
                      srcDoc={emailModal.preview.html}
                      className="mt-3 min-h-64 w-full rounded-xl border border-rule bg-white"
                    />
                  ) : (
                    <p className="mt-3 text-sm text-ink-2">Превью недоступно</p>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {confirmOpen ? (
        <div
          className="fixed inset-0 z-[400] flex items-center justify-center bg-ink/40 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-send-title"
        >
          <div className="w-full max-w-md rounded-2xl bg-paper p-6">
            <div className="flex items-start justify-between gap-3">
              <h2 id="confirm-send-title" className="text-2xl font-semibold">
                Подтвердите отправку
              </h2>
              <button
                type="button"
                className="inline-flex min-h-11 min-w-11 items-center justify-center"
                aria-label="Закрыть"
                onClick={() => setConfirmOpen(false)}
              >
                ✕
              </button>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-ink-2">
              Будет создан новый выпуск и записана stub-отправка. Живая почта не используется. Материалов:{' '}
              {approvedReady.length}.
            </p>
            <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                className="inline-flex min-h-11 items-center justify-center rounded-full border border-rule px-4 text-sm"
                disabled={sending}
                onClick={() => setConfirmOpen(false)}
              >
                Не отправлять
              </button>
              <button
                type="button"
                className="inline-flex min-h-11 items-center justify-center rounded-full bg-[oklch(45%_0.13_155)] px-4 text-sm font-medium text-paper disabled:opacity-55"
                disabled={sending}
                onClick={confirmSend}
              >
                Подтвердить отправку
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}

/**
 * Material preview modal — shortlist DTO only (D-01); order D-05; empty body D-06.
 * @param {{ item: import('../services/adminApi.js').AdminShortlistItem, onClose: () => void }} props
 */
function AdminItemPreview({ item, onClose }) {
  const body = typeof item.body_markdown === 'string' ? item.body_markdown.trim() : ''
  const provenance =
    typeof item.provenance_label === 'string' ? item.provenance_label.trim() : ''
  const charCount = Number.isFinite(item.char_count) ? item.char_count : 0
  const wordCount = Number.isFinite(item.word_count) ? item.word_count : 0
  const readingMinutes = Number.isFinite(item.reading_minutes) ? item.reading_minutes : 1
  const slug = typeof item.slug === 'string' ? item.slug.trim() : ''

  return (
    <div
      className="fixed inset-0 z-[400] flex items-center justify-center bg-ink/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="item-preview-title"
    >
      <div className="flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl bg-paper">
        <div className="flex shrink-0 items-start justify-between gap-3 px-6 pt-6">
          <h2 id="item-preview-title" className="text-2xl font-semibold">
            Превью материала
          </h2>
          <button
            type="button"
            className="inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center"
            aria-label="Закрыть"
            onClick={onClose}
          >
            ✕
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-6 pb-6">
          <p className="mt-4 break-words text-base font-semibold text-ink">{item.title}</p>
          {provenance ? (
            <p className="mt-2 break-words text-xs font-semibold text-muted">{provenance}</p>
          ) : null}
          <p className="mt-2 text-xs font-normal text-muted">
            ~{charCount} символов · {wordCount} слов · ~{readingMinutes} мин
          </p>
          {body ? (
            <div
              data-testid="admin-material-preview-body"
              className="prose-column mt-4 max-w-none break-words text-base leading-relaxed text-ink-2 [&_h2]:mt-4 [&_h2]:font-display [&_h2]:text-2xl [&_h2]:font-semibold [&_h2]:text-ink [&_p]:mt-3"
            >
              <Markdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeSlug, rehypeSanitize]}
              >
                {body}
              </Markdown>
            </div>
          ) : (
            <p className="mt-4 text-base text-muted">Текст материала недоступен</p>
          )}
          {slug ? (
            <Link
              to={`/materials/${slug}`}
              className="mt-6 inline-flex min-h-11 items-center font-medium text-accent hover:underline"
            >
              Открыть материал →
            </Link>
          ) : null}
        </div>
      </div>
    </div>
  )
}
