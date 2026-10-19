import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import TopicBallot from '../components/TopicBallot.jsx'
import ActionButton from '../components/ActionButton.jsx'
import ErrorPanel from '../components/ErrorPanel.jsx'
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
import {
  BallotFetchError,
  VoteSubmitError,
  armFailNextVoteSubmit,
  clearFailNextBallotFetch,
  fetchBallot,
  submitVote,
} from '../services/votingApi.js'
import { leaderStripText, voteButtonLabel, voteStatusText } from '../utils/voting.js'

const FALLBACK_CYCLE = {
  label: 'Цикл голосования',
  period: '',
  closesOn: 'закрытия цикла',
  progressRatio: 0,
  status: 'open',
}

const TOAST_DISMISS_MS = 4000

function applySnapshot(snapshot, setters) {
  const {
    setTopics,
    setLeaders,
    setCycleMeta,
    setConfirmedId,
    setSelectedId,
    setExpectedUpdatedAt,
  } = setters
  const topics = snapshot?.topics ?? []
  setTopics(topics)
  setLeaders(Array.isArray(snapshot?.leaders) ? snapshot.leaders : [])

  const cycle = snapshot?.cycle
  if (cycle) {
    setCycleMeta({
      label: cycle.label ?? FALLBACK_CYCLE.label,
      period: cycle.period ?? '',
      closesOn: cycle.closesOn ?? FALLBACK_CYCLE.closesOn,
      progressRatio: cycle.progress_ratio ?? cycle.progressRatio ?? 0,
      status: cycle.status ?? 'open',
    })
  } else {
    setCycleMeta({ ...FALLBACK_CYCLE, status: null })
  }

  const personal = snapshot?.personal_vote ?? null
  const confirmed = personal?.topic_id ?? null
  setConfirmedId(confirmed)
  setExpectedUpdatedAt(personal?.updated_at ?? null)
  // D-46: radios mirror server vote after confirm/load; never-voted stays empty
  setSelectedId(confirmed)
}

function EmptyVotingCta() {
  return (
    <p className="mt-6">
      <Link
        to="/"
        className="inline-flex min-h-11 items-center font-medium text-accent no-underline hover:underline"
      >
        К выпуску →
      </Link>
    </p>
  )
}

function votingFlags({ loadState, cycleMeta, topics, buttonState, selectedId, confirmedId }) {
  const cycleClosed = cycleMeta.status === 'closed'
  const noCycle = loadState === 'ready' && cycleMeta.status === null
  const noTopics = loadState === 'ready' && cycleMeta.status === 'open' && topics.length === 0
  const showBallot = loadState === 'ready' && !noCycle && !noTopics && topics.length > 0
  const confirmDisabled =
    loadState !== 'ready' ||
    cycleClosed ||
    buttonState === 'loading' ||
    !selectedId ||
    selectedId === confirmedId
  return { cycleClosed, noCycle, noTopics, showBallot, confirmDisabled }
}

function voteFailurePlan(err) {
  const voteError =
    err instanceof VoteSubmitError
      ? err
      : new VoteSubmitError('Не удалось сохранить голос.', { code: 'UNKNOWN' })
  if (voteError.code === 'NO_TOPIC') return { kind: 'validation', voteError }
  if (voteError.code === 'CYCLE_CLOSED' && voteError.ballot) return { kind: 'closed', voteError }
  if (voteError.code === 'VOTE_CONFLICT' && voteError.ballot) return { kind: 'conflict', voteError }
  return { kind: 'save-error', voteError }
}

function conflictBannerText(voteError) {
  const serverTitle = topicTitleById(
    voteError.ballot.topics ?? [],
    voteError.ballot.personal_vote?.topic_id,
  )
  if (!serverTitle) {
    return 'Голос уже изменён на другом устройстве. Показан актуальный выбор сервера.'
  }
  return `Голос уже изменён на другом устройстве. На сервере: «${serverTitle}».`
}

function topicTitleById(topics, topicId) {
  if (!topicId) return null
  return topics.find((t) => t.id === topicId)?.title ?? null
}

export default function VotingPage() {
  const [searchParams] = useSearchParams()
  const [topics, setTopics] = useState([])
  const [leaders, setLeaders] = useState([])
  const [cycleMeta, setCycleMeta] = useState(FALLBACK_CYCLE)
  const [selectedId, setSelectedId] = useState(null)
  const [confirmedId, setConfirmedId] = useState(null)
  const [expectedUpdatedAt, setExpectedUpdatedAt] = useState(null)
  const [loadState, setLoadState] = useState('loading')
  const [loadKey, setLoadKey] = useState(0)
  const [buttonState, setButtonState] = useState('idle')
  const [toast, setToast] = useState('')
  const [error, setError] = useState(null)
  const [conflictBanner, setConflictBanner] = useState('')
  const [validationMessage, setValidationMessage] = useState('')
  const [attemptCount, setAttemptCount] = useState(0)
  const [armedFailOnce] = useState(() => {
    const shouldFail = searchParams.get('simulateError') === '1'
    if (shouldFail) armFailNextVoteSubmit()
    return shouldFail
  })

  const snapshotSetters = {
    setTopics,
    setLeaders,
    setCycleMeta,
    setConfirmedId,
    setSelectedId,
    setExpectedUpdatedAt,
  }

  const reloadBallot = useCallback(() => {
    clearFailNextBallotFetch()
    setError(null)
    setLoadKey((k) => k + 1)
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoadState('loading')
    fetchBallot()
      .then((snapshot) => {
        if (cancelled) return
        applySnapshot(snapshot, snapshotSetters)
        setLoadState('ready')
      })
      .catch((err) => {
        if (cancelled) return
        const fetchError =
          err instanceof BallotFetchError
            ? err
            : new BallotFetchError('Не удалось загрузить голосование.', { code: 'UNKNOWN' })
        setError({
          title: 'Ошибка загрузки',
          message: fetchError.message,
          code: fetchError.code,
          retryable: fetchError.retryable,
        })
        setLoadState('error')
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload via loadKey only
  }, [loadKey])

  // D-45: toast fades after ~3–5s (PlatformProofBanner pattern)
  useEffect(() => {
    if (!toast) return undefined
    const timer = window.setTimeout(() => setToast(''), TOAST_DISMISS_MS)
    return () => window.clearTimeout(timer)
  }, [toast])

  const status = useMemo(
    () =>
      voteStatusText({
        confirmedId,
        selectedId,
        topics,
      }),
    [confirmedId, selectedId, topics],
  )

  const { cycleClosed, noCycle, noTopics, showBallot, confirmDisabled } = votingFlags({
    loadState,
    cycleMeta,
    topics,
    buttonState,
    selectedId,
    confirmedId,
  })

  async function confirmVote() {
    if (buttonState === 'loading' || cycleClosed) return

    if (!selectedId) {
      setValidationMessage('Выберите тему')
      setError(null)
      return
    }

    setValidationMessage('')
    setButtonState('loading')
    setToast('')
    setError(null)
    setConflictBanner('')
    setAttemptCount((count) => count + 1)

    const hadConfirmed = Boolean(confirmedId)

    try {
      const snapshot = await submitVote(selectedId, expectedUpdatedAt)
      applySnapshot(snapshot, snapshotSetters)
      setButtonState('idle')
      setToast(hadConfirmed ? 'Голос изменён' : 'Голос сохранён')
      setAttemptCount(0)
    } catch (err) {
      const plan = voteFailurePlan(err)
      const { voteError } = plan
      if (plan.kind === 'validation') {
        setValidationMessage(voteError.message || 'Выберите тему')
        setButtonState('idle')
        return
      }
      if (plan.kind === 'closed') {
        applySnapshot(voteError.ballot, snapshotSetters)
        setButtonState('idle')
        setError(null)
        return
      }
      if (plan.kind === 'conflict') {
        applySnapshot(voteError.ballot, snapshotSetters)
        setConflictBanner(conflictBannerText(voteError))
        setButtonState('idle')
        setError(null)
        return
      }
      setButtonState(voteError.retryable ? 'error' : 'idle')
      setError({
        title: 'Ошибка сохранения',
        message: voteError.message,
        code: voteError.code,
        retryable: voteError.retryable,
      })
    }
  }

  function clearError() {
    setError(null)
    if (buttonState === 'error') setButtonState('idle')
  }

  const leaderCopy = showBallot || cycleClosed ? leaderStripText(leaders) : null

  function selectTopic(id) {
    if (cycleClosed) return
    setSelectedId(id)
    setValidationMessage('')
    setConflictBanner('')
    if (buttonState === 'success' || buttonState === 'error') setButtonState('idle')
    if (error) setError(null)
  }

  // D-55: GET failure → full ServiceUnavailable splash (not ErrorPanel-only)
  if (loadState === 'error') {
    return <VotingUnavailable onRetry={reloadBallot} />
  }

  return (
    <section className="max-w-3xl" data-testid="voting-page">
      <h1 className="mb-6 font-display text-3xl font-semibold">Голосование за тему разбора</h1>
      <VotingEmptyNotices noCycle={noCycle} noTopics={noTopics} />
      {showBallot || cycleClosed ? (
        <VotingBallotPanel
          cycleClosed={cycleClosed}
          conflictBanner={conflictBanner}
          cycleMeta={cycleMeta}
          loadState={loadState}
          status={status}
          armedFailOnce={armedFailOnce}
          leaderCopy={leaderCopy}
          topics={topics}
          selectedId={selectedId}
          onSelect={selectTopic}
          validationMessage={validationMessage}
          error={error}
          attemptCount={attemptCount}
          clearError={clearError}
          toast={toast}
          confirmDisabled={confirmDisabled}
          confirmVote={confirmVote}
          buttonState={buttonState}
          confirmedId={confirmedId}
        />
      ) : null}
      {loadState === 'loading' ? (
        <p className="text-sm text-ink-2" role="status" aria-live="polite">
          Загрузка…
        </p>
      ) : null}
    </section>
  )
}

function VotingUnavailable({ onRetry }) {
  return (
    <section className="max-w-3xl" data-testid="voting-page">
      <h1 className="mb-6 font-display text-3xl font-semibold">Голосование за тему разбора</h1>
      <ServiceUnavailable onRetry={onRetry} />
    </section>
  )
}

function VotingEmptyNotices({ noCycle, noTopics }) {
  return (
    <>
      {noCycle ? (
        <div data-testid="voting-no-cycle">
          <p className="max-w-prose text-ink-2">Сейчас нет активного голосования</p>
          <EmptyVotingCta />
        </div>
      ) : null}
      {noTopics ? (
        <div data-testid="voting-no-topics">
          <h2 className="font-display text-2xl font-semibold">Темы ещё не объявлены</h2>
          <p className="mt-3 max-w-prose text-ink-2">Когда редакция откроет темы, они появятся здесь.</p>
          <EmptyVotingCta />
        </div>
      ) : null}
    </>
  )
}

function VotingBallotPanel({
  cycleClosed,
  conflictBanner,
  cycleMeta,
  loadState,
  status,
  armedFailOnce,
  leaderCopy,
  topics,
  selectedId,
  onSelect,
  validationMessage,
  error,
  attemptCount,
  clearError,
  toast,
  confirmDisabled,
  confirmVote,
  buttonState,
  confirmedId,
}) {
  return (
    <>
      {cycleClosed ? (
        <div
          data-testid="voting-closed-banner"
          className="mb-6 rounded-2xl border border-rule bg-paper-2 p-5 text-sm text-ink-2"
        >
          Цикл голосования закрыт
        </div>
      ) : null}
      {conflictBanner ? (
        <div
          data-testid="vote-conflict-banner"
          className="mb-6 rounded-2xl border border-rule bg-paper-2 p-5 text-sm text-ink-2"
          role="alert"
        >
          {conflictBanner}
        </div>
      ) : null}
      <VotingCycleCard
        cycleMeta={cycleMeta}
        loadState={loadState}
        status={status}
        armedFailOnce={armedFailOnce}
        cycleClosed={cycleClosed}
      />

          {leaderCopy ? (
            <div
              data-testid="leader-strip"
              className="mb-6 rounded-2xl border border-rule bg-paper-2 p-5 text-sm text-ink-2"
            >
              {leaderCopy}
            </div>
          ) : null}

          <TopicBallot
            topics={topics}
            selectedId={selectedId}
            disabled={cycleClosed}
            onSelect={onSelect}
          />

          {!cycleClosed ? (
            <VotingConfirmBar
              validationMessage={validationMessage}
              loadState={loadState}
              selectedId={selectedId}
              error={error}
              attemptCount={attemptCount}
              clearError={clearError}
              toast={toast}
              confirmDisabled={confirmDisabled}
              confirmVote={confirmVote}
              buttonState={buttonState}
              confirmedId={confirmedId}
            />
          ) : null}
    </>
  )
}

function ballotStatusCopy(loadState, status) {
  if (loadState === 'loading') return 'Загрузка…'
  return status
}

function VotingCycleCard({ cycleMeta, loadState, status, armedFailOnce, cycleClosed }) {
  return (
    <>
      <div className="mb-8 rounded-2xl border border-rule bg-[oklch(98.5%_0.009_95)] p-5">
        <div className="mb-3 flex items-baseline justify-between gap-3">
          <span className="text-xs uppercase tracking-wide text-muted">{cycleMeta.label}</span>
          <span className="text-xs text-ink-2">{cycleMeta.period}</span>
        </div>
        <div className="h-1 overflow-hidden rounded bg-[oklch(93%_0.035_78)]">
          <div
            className="h-full bg-voting"
            style={{ width: `${Math.round(cycleMeta.progressRatio * 100)}%` }}
          />
        </div>
        <p className="mt-3 text-sm text-ink-2" role="status" aria-live="polite">
          {ballotStatusCopy(loadState, status)}
        </p>
        {armedFailOnce && !cycleClosed ? (
          <p className="mt-2 text-xs text-muted">
            Демо режима сбоя: первая отправка будет отклонена сервером (повторите).
          </p>
        ) : null}
      </div>
      {cycleClosed ? (
        <p className="mb-8 text-sm text-ink-2">Результаты цикла (только чтение).</p>
      ) : (
        <p className="mb-8 text-sm text-ink-2">
          Один голос за цикл. Вы можете изменить выбор до {cycleMeta.closesOn}.
        </p>
      )}
    </>
  )
}

function voteErrorMeta(error, attemptCount) {
  if (error.retryable) {
    return `Попытка ${attemptCount}. Код: ${error.code}. Можно повторить.`
  }
  return `Код: ${error.code}`
}

function VotingConfirmBar({
  validationMessage,
  loadState,
  selectedId,
  error,
  attemptCount,
  clearError,
  toast,
  confirmDisabled,
  confirmVote,
  buttonState,
  confirmedId,
}) {
  const needsTopic = loadState === 'ready' && !selectedId
  return (
    <div className="sticky bottom-0 mt-8 flex flex-wrap items-center justify-end gap-3 border-t border-rule bg-paper/95 py-3 backdrop-blur">
      {validationMessage || needsTopic ? (
        <p className="text-sm text-[oklch(45%_0.14_25)]" role="alert">
          {validationMessage || 'Выберите тему'}
        </p>
      ) : null}
      {error ? (
        <ErrorPanel
          title={error.title}
          message={error.message}
          meta={voteErrorMeta(error, attemptCount)}
          onDismiss={clearError}
        />
      ) : null}
      {toast ? (
        <p
          data-testid="vote-toast"
          className="text-sm text-[oklch(45%_0.13_155)]"
          aria-live="polite"
        >
          {toast}
        </p>
      ) : null}
      <ActionButton
        data-testid="confirm-vote"
        variant="voting"
        state={buttonState}
        disabled={confirmDisabled}
        onClick={confirmVote}
      >
        {voteButtonLabel(buttonState, { confirmedId })}
      </ActionButton>
    </div>
  )
}
