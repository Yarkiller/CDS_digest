# Responsive evidence (homework Step 6)

Screenshots captured by Playwright during `tests/web-app.spec.js` (`web app responsive`).

| File | Viewport | Page |
|------|----------|------|
| `mobile-320-issue.png` | 320×568 | `/` |
| `mobile-390-issue.png` | 390×844 | `/` |
| `mobile-390-voting.png` | 390×844 | `/voting` |
| `desktop-1280-issue.png` | 1280×800 | `/` |
| `mobile-320-issue-light.png` | 320×568 | `/` (светлая тема) |
| `mobile-390-issue-light.png` | 390×844 | `/` (светлая тема) |
| `mobile-390-voting-light.png` | 390×844 | `/voting` (светлая тема) |
| `desktop-1280-issue-light.png` | 1280×800 | `/` (светлая тема) |

Assertions: no horizontal overflow; mobile hides «Мария Сидорова»; desktop shows identity + wider search; voting confirm stays in viewport on phone.
