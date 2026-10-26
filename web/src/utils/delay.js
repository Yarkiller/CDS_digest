/** Shared simulated network latency for UI loading states (ms). */
export const UI_LATENCY_MS = 600

export function delay(ms = UI_LATENCY_MS) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}
