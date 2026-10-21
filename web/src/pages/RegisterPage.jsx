import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import ErrorPanel from '../components/ErrorPanel.jsx'
import { AuthApiError, getSignUpInvocationCount, signUp, updateAuthDisplayName } from '../services/authApi.js'
import { sanitizeReturnUrl } from '../services/authEnv.js'
import { isAllowedCorporateEmail } from '../services/emailDomain.js'
import { corporateAllowedDomains } from '../services/oauthSession.js'
import { MeApiError, updateDisplayName } from '../services/meApi.js'
import { armWelcomeToast } from '../services/welcomeSession.js'

const DOMAIN_MESSAGE = 'Вход только с корпоративного домена СВА'
const CONFIRM_MESSAGE =
  'Регистрация завершена. Аккаунт активен — войдите.'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [loginNickname, setLoginNickname] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [domainError, setDomainError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({
    loginNickname: '',
    email: '',
    password: '',
  })
  const [networkError, setNetworkError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [signUpCalls, setSignUpCalls] = useState(getSignUpInvocationCount())

  async function handleSubmit(event) {
    event.preventDefault()
    setNetworkError(null)

    const nextFieldErrors = {
      loginNickname: loginNickname.trim() ? '' : 'Заполните поле',
      email: email.trim() ? '' : 'Заполните поле',
      password: password ? '' : 'Заполните поле',
    }
    setFieldErrors(nextFieldErrors)
    if (nextFieldErrors.loginNickname || nextFieldErrors.email || nextFieldErrors.password) {
      return
    }

    if (!isAllowedCorporateEmail(email.trim(), corporateAllowedDomains(import.meta.env))) {
      setDomainError(DOMAIN_MESSAGE)
      setSignUpCalls(getSignUpInvocationCount())
      return
    }
    setDomainError('')

    setSubmitting(true)
    try {
      const nickname = loginNickname.trim()
      const session = await signUp({
        email: email.trim(),
        password,
        displayName: nickname,
      })
      setSignUpCalls(getSignUpInvocationCount())
      if (!session) {
        setNetworkError({ message: CONFIRM_MESSAGE, retryable: false })
        return
      }
      await updateDisplayName(nickname)
      await updateAuthDisplayName(nickname)
      armWelcomeToast()
      const dest = sanitizeReturnUrl(searchParams.get('returnUrl'))
      navigate(dest, { replace: true })
    } catch (err) {
      setSignUpCalls(getSignUpInvocationCount())
      const message =
        err instanceof AuthApiError || err instanceof MeApiError
          ? err.message
          : 'Сервис входа временно недоступен. Проверьте соединение и повторите попытку.'
      const retryable =
        err instanceof AuthApiError || err instanceof MeApiError ? err.retryable : true
      setNetworkError({ message, retryable })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-bg-app px-4 text-text-primary">
      <div className="w-full max-w-md rounded-2xl border border-border bg-bg-surface p-8 shadow-sm">
        <header className="mb-8 text-center">
          <h1 className="font-display text-3xl font-semibold text-primary-text">Digest CDS</h1>
          <p className="mt-1 text-xs uppercase tracking-wide text-text-disabled">СВА · внутреннее издание</p>
        </header>

        <form className="flex flex-col gap-5" onSubmit={handleSubmit} noValidate>
          {networkError ? (
            <div className="flex flex-col gap-2">
              <ErrorPanel
                title={
                  networkError.retryable
                    ? 'Сервис входа временно недоступен'
                    : 'Регистрация'
                }
                message={networkError.message}
                onDismiss={() => setNetworkError(null)}
              />
              {networkError.retryable ? (
                <button
                  type="submit"
                  className="min-h-11 self-start rounded-full bg-primary-solid px-4 text-sm text-on-solid"
                  disabled={submitting}
                >
                  Повторить
                </button>
              ) : null}
            </div>
          ) : null}

          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="login-nickname">
              Логин
            </label>
            <input
              id="login-nickname"
              name="login-nickname"
              type="text"
              autoComplete="nickname"
              placeholder="Как вас показывать в шапке"
              aria-invalid={Boolean(fieldErrors.loginNickname) || undefined}
              className="min-h-11 w-full rounded-xl border border-field-border bg-bg-app px-3 text-sm"
              value={loginNickname}
              onChange={(e) => {
                setLoginNickname(e.target.value)
                if (fieldErrors.loginNickname) {
                  setFieldErrors((f) => ({ ...f, loginNickname: '' }))
                }
              }}
              required
            />
            <p className="mt-1 text-xs text-text-disabled">
              Отображаемый ник для голосования — любое ненастоящее имя, не ФИО
            </p>
            {fieldErrors.loginNickname ? (
              <p className="mt-1 text-sm text-danger-ink" role="alert">
                {fieldErrors.loginNickname}
              </p>
            ) : null}
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="register-email">
              Email
            </label>
            <input
              id="register-email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="name@sberbank.ru"
              aria-describedby="register-email-help"
              aria-invalid={Boolean(domainError || fieldErrors.email) || undefined}
              className="min-h-11 w-full rounded-xl border border-field-border bg-bg-app px-3 text-sm"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                if (domainError) setDomainError('')
                if (fieldErrors.email) setFieldErrors((f) => ({ ...f, email: '' }))
              }}
              required
            />
            <p id="register-email-help" className="mt-1 text-xs text-text-disabled">
              Только @sberbank.ru или @omega.sbrf.ru
            </p>
            {fieldErrors.email ? (
              <p className="mt-1 text-sm text-danger-ink" role="alert">
                {fieldErrors.email}
              </p>
            ) : null}
            {domainError ? (
              <p className="mt-1 text-sm text-danger-ink" role="alert">
                {domainError}
              </p>
            ) : null}
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="register-password">
              Пароль
            </label>
            <input
              id="register-password"
              name="password"
              type="password"
              autoComplete="new-password"
              aria-invalid={Boolean(fieldErrors.password) || undefined}
              className="min-h-11 w-full rounded-xl border border-field-border bg-bg-app px-3 text-sm"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                if (fieldErrors.password) setFieldErrors((f) => ({ ...f, password: '' }))
              }}
              required
            />
            {fieldErrors.password ? (
              <p className="mt-1 text-sm text-danger-ink" role="alert">
                {fieldErrors.password}
              </p>
            ) : null}
          </div>

          <button
            type="submit"
            className="min-h-11 w-full rounded-full bg-primary-solid px-4 text-sm font-medium text-on-solid disabled:opacity-60"
            disabled={submitting}
          >
            {submitting ? 'Регистрация…' : 'Зарегистрироваться'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-text-secondary">
          Уже есть аккаунт?{' '}
          <Link to="/login" className="underline">
            Войти
          </Link>
        </p>
        <p className="mt-3 text-center text-xs text-text-disabled">
          Доступ: @sberbank.ru, @omega.sbrf.ru
        </p>

        <span
          data-testid="auth-sign-up-calls"
          data-count={String(signUpCalls)}
          className="hidden"
          aria-hidden="true"
        />
      </div>
    </div>
  )
}
