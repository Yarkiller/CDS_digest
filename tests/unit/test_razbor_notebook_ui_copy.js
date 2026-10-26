/**
 * Copy contract for RazborPage notebook dual strip (RAZB-03 / D-70…72).
 * Playwright enable/disable proofs land in 04-09.
 */
const fs = require('fs')
const path = require('path')

const pagePath = path.join(__dirname, '../../web/src/pages/RazborPage.jsx')
const apiPath = path.join(__dirname, '../../web/src/services/razboryApi.js')
const page = fs.readFileSync(pagePath, 'utf8')
const api = fs.readFileSync(apiPath, 'utf8')

const checks = [
  [/Скачать \.ipynb|Скачать \\.ipynb|ipynb/, page, 'RazborPage has download CTA / ipynb'],
  [/Notebook скоро будет/, page, 'RazborPage has missing-notebook caption'],
  [/Не удалось скачать/, page, 'RazborPage has download failure toast copy'],
  [/downloadRazborNotebook/, api, 'razboryApi exposes downloadRazborNotebook'],
]

let failed = false
for (const [re, source, label] of checks) {
  if (!re.test(source)) {
    console.error('FAIL:', label)
    failed = true
  } else {
    console.log('OK:', label)
  }
}

if (failed) process.exit(1)
console.log('notebook UI copy contract passed')
