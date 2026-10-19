import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import ErrorPanel from '../components/ErrorPanel.jsx'
import {
  AuthApiError,
  getSignInInvocationCount,
  signIn,
} from '../services/authApi.js'
import { sanitizeReturnUrl } from '../services/authEnv.js'
import { isAllowedCorporateEmail } from '../services/emailDomain.js'
import { armWelcomeToast } from '../services/welcomeSession.js'

const DOMAIN_MESSAGE = 'Вход только с корпоративного домена СВА'

export default function LoginPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [domainError, setDomainError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({ email: '', password: '' })
  const [networkError, setNetworkError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [signInCalls, setSignInCalls] = useState(getSignInInvocationCount())

  async function handleSubmit(event) {
    event.preventDefault()
    setNetworkError(null)

    const nextFieldErrors = {
      email: email.trim() ? '' : 'Заполните поле',
      password: password ? '' : 'Заполните поле',
    }
    setFieldErrors(nextFieldErrors)
    if (nextFieldErrors.email || nextFieldErrors.password) {
      return
    }

    if (!isAllowedCorporateEmail(email.trim())) {
      setDomainError(DOMAIN_MESSAGE)
      setSignInCalls(getSignInInvocationCount())
      return
    }
    setDomainError('')

    setSubmitting(true)
    try {
      await signIn({ email: email.trim(), password })
      setSignInCalls(getSignInInvocationCount())
      armWelcomeToast()
      const dest = sanitizeReturnUrl(searchParams.get('returnUrl'))
      navigate(dest, { replace: true })
    } catch (err) {
      setSignInCalls(getSignInInvocationCount())
      const message =
        err instanceof AuthApiError
          ? err.message
          : 'Сервис входа временно недоступен. Проверьте соединение и повторите попытку.'
      const retryable = err instanceof AuthApiError ? err.retryable : true
      setNetworkError({ message, retryable })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-paper px-4 text-ink">
      <div className="w-full max-w-md rounded-2xl border border-rule bg-paper-2 p-8 shadow-sm">
        <header className="mb-8 text-center">
          <h1 className="font-display text-3xl font-semibold text-accent">Digest CDS</h1>
          <p className="mt-1 text-xs uppercase tracking-wide text-muted">СВА · внутреннее издание</p>
        </header>

        <form className="flex flex-col gap-5" onSubmit={handleSubmit} noValidate>
          {networkError ? (
            <div className="flex flex-col gap-2">
              <ErrorPanel
                title="Сервис входа временно недоступен"
                message={networkError.message}
                onDismiss={() => setNetworkError(null)}
              />
              {networkError.retryable ? (
                <button
                  type="submit"
                  className="min-h-11 self-start rounded-full bg-accent px-4 text-sm text-accent-ink"
                  disabled={submitting}
                >
                  Повторить
                </button>
              ) : null}
            </div>
          ) : null}

          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="name@sberbank.ru"
              aria-describedby="email-help"
              aria-invalid={Boolean(domainError || fieldErrors.email) || undefined}
              className="min-h-11 w-full rounded-xl border border-rule bg-paper px-3 text-sm"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                if (domainError) setDomainError('')
                if (fieldErrors.email) setFieldErrors((f) => ({ ...f, email: '' }))
              }}
              required
            />
            <p id="email-help" className="mt-1 text-xs text-muted">
              Только @sberbank.ru или @omega.sbrf.ru
            </p>
            {fieldErrors.email ? (
              <p className="mt-1 text-sm text-[oklch(45%_0.14_25)]" role="alert">
                {fieldErrors.email}
              </p>
            ) : null}
            {domainError ? (
              <p className="mt-1 text-sm text-[oklch(45%_0.14_25)]" role="alert">
                {domainError}
              </p>
            ) : null}
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="password">
              Пароль
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              aria-invalid={Boolean(fieldErrors.password) || undefined}
              className="min-h-11 w-full rounded-xl border border-rule bg-paper px-3 text-sm"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                if (fieldErrors.password) setFieldErrors((f) => ({ ...f, password: '' }))
              }}
              required
            />
            {fieldErrors.password ? (
              <p className="mt-1 text-sm text-[oklch(45%_0.14_25)]" role="alert">
                {fieldErrors.password}
              </p>
            ) : null}
          </div>

          <button
            type="submit"
            className="min-h-11 w-full rounded-full bg-accent px-4 text-sm font-medium text-accent-ink disabled:opacity-60"
            disabled={submitting}
          >
            {submitting ? 'Вход…' : 'Войти'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-ink-2">
          Нет аккаунта?{' '}
          <Link to="/register" className="underline">
            Регистрация
          </Link>
        </p>
        <p className="mt-3 text-center text-xs text-muted">
          Доступ: @sberbank.ru, @omega.sbrf.ru
        </p>

        <span
          data-testid="auth-sign-in-calls"
          data-count={String(signInCalls)}
          className="hidden"
          aria-hidden="true"
        />
      </div>
    </div>
  )
}
