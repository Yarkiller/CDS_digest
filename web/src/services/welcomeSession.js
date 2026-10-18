/** Session flag: show welcome toast once after login/register. */
const WELCOME_KEY = '__DIGEST_SHOW_WELCOME__'

export function armWelcomeToast() {
  if (typeof sessionStorage === 'undefined') return
  sessionStorage.setItem(WELCOME_KEY, '1')
}

export function peekWelcomeToast() {
  if (typeof sessionStorage === 'undefined') return false
  return sessionStorage.getItem(WELCOME_KEY) === '1'
}

export function clearWelcomeToast() {
  if (typeof sessionStorage === 'undefined') return
  sessionStorage.removeItem(WELCOME_KEY)
}
