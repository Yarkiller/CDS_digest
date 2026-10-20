#!/usr/bin/env node
/**
 * Cross-platform JS unit runner (node:test).
 *
 * `node --test "tests/unit/**\/*.js"` relies on the shell or on node's own glob
 * support, and the repo is run from PowerShell, cmd and bash. Enumerating the
 * files here keeps `npm run test:js` identical everywhere, including CI.
 */
const { readdirSync } = require('node:fs')
const { join } = require('node:path')
const { spawnSync } = require('node:child_process')

const unitDir = join(__dirname, '..', 'tests', 'unit')
const files = readdirSync(unitDir)
  .filter((name) => name.endsWith('.js'))
  .sort()
  .map((name) => join(unitDir, name))

if (files.length === 0) {
  console.error(`no JS unit tests found in ${unitDir}`)
  process.exit(1)
}

const result = spawnSync(process.execPath, ['--test', ...files], { stdio: 'inherit' })
process.exit(result.status ?? 1)
