# Phase 17: YAML merge-key acceptance in the strict validator - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-14
**Phase:** 17-yaml-merge-key-acceptance-in-the-strict-validator
**Areas discussed:** Merge idiom, Duplicate-key strictness, DoS bound, Error copy, Extra-key copy, Editor hint

---

## Merge idiom

| Option | Description | Selected |
|--------|-------------|----------|
| Parse-only fix, schema untouched | Merge accepted where it yields exactly the 4 keys; the `defaults:` + `<<: *base` reuse style still rejected, but honestly. D-01/D-02/D-06 preserved | ✓ |
| Also tolerate one anchor-holder key | Widen the locked schema and add an explicit "which extra key is allowed" rule so real reuse works | |
| Redefine the phase as "named anchors" | Treat reuse as the actual need; bigger, likely its own phase | |

**User's choice:** Parse-only fix, schema untouched
**Notes:** Before the question the assistant surfaced that under the locked 4-key `extra="forbid"`
schema a merge key is nearly pointless: the only merge shape that yields a valid config is `<<: &base`
with the same four keys inline, while the whole reason to use merge — *reuse* (`<<: *base`) — needs an
anchor holder key that the schema rejects. Verified by reproduction during the discussion, so the
decision was made with that consequence on the table.

---

## Duplicate-key strictness (emerged from the idiom answer)

| Option | Description | Selected |
|--------|-------------|----------|
| YAML spec semantics | Merge-introduced collisions are not errors; first source wins; an explicit own key overrides a merged one. Explicit duplicates stay an absolute reject (PIPE-02 intact) | ✓ |
| Strict for everything post-merge | Any post-merge collision is a reject, so "duplicate = reject" stays absolute — but `<<: *base` + explicit override would also fail | |
| Middle ground | Explicit override allowed, `<<: [*a, *b]` with a shared key rejected | |

**User's choice:** YAML spec semantics
**Notes:** Framed as the crux of "don't weaken duplicate-key rejection": after flattening,
merge-introduced collisions look like duplicates, so getting this wrong either breaks legitimate
overrides or weakens the duplicate rule.

---

## DoS bound

| Option | Description | Selected |
|--------|-------------|----------|
| Both bounds, reject before the heavy work | Merge depth/fan-out **and** a flattened-entry budget, enforced before flattening (defence in depth, no false rejects) | ✓ |
| Flattened-entry budget only | One honest metric covering both fan-out and depth | |
| Depth + fan-out only | Structural check before expansion | |

**User's choice:** Both bounds, reject before the heavy work
**Notes:** Measurements presented in the question: fan-out 3, **457 chars → 5.26 s**, cost ≈ ×3 per
level (levels 12/13/14 → 0.70 s / 1.87 s / 5.26 s), all under the 20 000-char source cap, which provides
no protection here. Also agreed that any new pre-pass (`yaml.compose`/node walk) must be wrapped in the
existing `RecursionError`/`yaml.YAMLError` mapping so it cannot become a new 500 path.

---

## Error copy (bound breach)

| Option | Description | Selected |
|--------|-------------|----------|
| New dedicated message | «Документ содержит слияние (merge), превышающее допустимый размер» — honest about what was breached | ✓ |
| Reuse the over-cap message | «Документ конфига превышает допустимый размер» — no new string, but false for a ~500-char document | |
| Claude's choice | Leave the wording to Claude | |

**User's choice:** New dedicated message

---

## Extra key copy (emerged from the idiom answer)

| Option | Description | Selected |
|--------|-------------|----------|
| Russian message that teaches the form | «Лишний ключ «defaults»: якоря нужно объявлять в самом `<<`» (key name interpolated) | ✓ |
| Keep Pydantic's English message | «Extra inputs are not permitted» — consistent with all other schema errors, minimal scope | |
| Claude's choice | Leave it to Claude | |

**User's choice:** Russian message that teaches the form
**Notes:** Flagged that under the parse-only decision the natural anchor-holder style is *the most likely*
admin mistake after the fix, so leaving it English would reintroduce exactly the cryptic error this phase
exists to remove.

---

## Editor hint

| Option | Description | Selected |
|--------|-------------|----------|
| No hint | Pure server-side fix | |
| Add hint text | Would need a UI-SPEC touch + Playwright RED test | |
| Defer to the backlog | Record it as its own future item | ✓ |

**User's choice:** Defer to the backlog
**Notes:** A hint advertising `<<` support would be dishonest while anchor reuse does not work (D-01).

---

## Claude's Discretion

- Numeric values of both bounds (depth/fan-out limit, flattened-entry budget).
- Pre-pass mechanics (`yaml.compose` + node walk vs. counting `construct_mapping`).
- Placement of the new constants and message strings.
- Test organisation; the `yaml.SafeLoader` oracle loop is required regardless.

## Deferred Ideas

- **Editor hint about `<<` support** — becomes honest only if the schema is ever widened. Candidate
  backlog item for `/gsd-review-backlog`; needs a `16-UI-SPEC.md` A-1 editor-section touch and a
  Playwright RED test if picked up.
