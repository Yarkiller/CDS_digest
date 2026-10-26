# Requirements (from PRDs)

Sources: `docs/digest-cds/user_stories.md` (descriptions/priorities) + `docs/digest-cds/acceptance_criteria.md` (Given/When/Then). Same US IDs treated as complementary layers, not competing variants.

## REQ-US-01
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как сотрудник СВА (или любая роль), я хочу войти с корпоративного email `@sberbank.ru` / `@omega.sbrf.ru`, чтобы получить доступ к Digest CDS. (Must)
- acceptance: Valid corporate email + credentials → session and access; non-allowed domain rejected with inline domain message and no session; empty email/password → inline validation, no auth API call.
- scope: login, email domain restriction

## REQ-US-02
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как авторизованный пользователь, я хочу после входа сразу попасть на текущий выпуск, чтобы начать чтение без лишней навигации. (Must)
- acceptance: Login without returnUrl → current issue; deep-link/email link with returnUrl → return to original URL after login.
- scope: login redirect, issue

## REQ-US-03
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как рядовой сотрудник СВА, я хочу открыть текущий выпуск с обложкой и оглавлением, чтобы за минуту понять состав дайджеста. (Must)
- acceptance: Published issue with materials → number/period, title, IssueTOC; empty published materials → empty state «выпуск готовится» with CTA to archive/KB.
- scope: issue, IssueTOC

## REQ-US-04
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как рядовой сотрудник СВА, я хочу увидеть редакционный callout о цикле голосования, чтобы знать срок и перейти к выбору темы. (Must)
- acceptance: Open voting cycle → EditorialCallout with end date and CTA to voting; closed cycle → closed messaging, no topic-select CTA.
- scope: issue, voting cycle callout

## REQ-US-05
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как рядовой сотрудник СВА, я хочу видеть под заголовком материала короткое «зачем СВА» без жаргона, чтобы оценить пользу до чтения статьи. (Should)
- acceptance: Material with audit-dek → 1–2 audit-language sentences under title; without audit-dek → hide or neutral editorial fallback, no empty stub line.
- scope: issue, audit-dek

## REQ-US-06
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как рядовой сотрудник СВА, я хочу получить выпуск также письмом со ссылкой на сайт, чтобы читать в привычном канале и углубляться в издании. (Nice)
- acceptance: After admin send → email contains link to corresponding issue/archive item; unauthenticated link → login then returnUrl to target issue.
- scope: email digest, issue

## REQ-US-07
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как рядовой сотрудник СВА, я хочу читать материал в prose-колонке с оглавлением, чтобы спокойно усвоить текст как в издании. (Must)
- acceptance: Open material → prepared article in prose + section TOC; no raw video/audio/transcript as material content; TOC click scrolls/navigates to section.
- scope: material, prose, TOC

## REQ-US-08
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как Data Analyst или Data Scientist, я хочу открыть подготовленную статью из выпуска / базы, чтобы изучить детали метода или приёма без просмотра исходного видео. (Must)
- acceptance: Select article material from issue/knowledge → material page with article content and distinguishable «статья» type; unknown id → «материал не найден» with back nav.
- scope: material, article format

## REQ-US-09
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как читатель, я хочу видеть, что материал является подготовленной статьёй, понимать его происхождение и переходить по ссылкам на связанные статьи, чтобы отличать анализ от исходного текста и разобраться в сложных терминах. (Should)
- acceptance: Article with provenance, ≥1 tag, related-term link → badge «Статья», tags, provenance, internal related link at first suitable mention; missing tags/related → badge still shown, no fabricated links, layout intact.
- scope: material, provenance, related articles

## REQ-US-10
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как рядовой сотрудник СВА, я хочу отдать один голос за тему в цикле голосования, чтобы влиять на тему ближайшего разбора. (Must)
- acceptance: Confirm vote in open cycle → exactly one vote saved and status «Ваш голос:» with topic; second independent vote without change still one vote; submit without selection → «Выберите тему», no send.
- scope: voting, one vote per cycle

## REQ-US-11
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как участник голосования, я хочу видеть честный статус «голос не отдан» без предвыбранной темы, чтобы не подтвердить чужой выбор по ошибке. (Must)
- acceptance: Open voting before voting → status vote not cast; no radio pre-selected; leading topic shown separately from personal choice.
- scope: voting, ballot UX

## REQ-US-12
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как участник голосования, я хочу изменить свой голос до закрытия окна цикла, чтобы исправить выбор при новой информации. (Must)
- acceptance: Change A→B while open → counters update, status B; after cycle closed → reject change with closed-cycle message.
- scope: voting, vote change

## REQ-US-13
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как рядовой сотрудник СВА, я хочу видеть краткое описание темы на языке аудита и число материалов, чтобы голосовать осознанно. (Should)
- acceptance: Ballot topics show audit-language description and material count (including explicit «0 материалов»); topic without description still shows count without misleading empty description block.
- scope: voting, topic metadata

## REQ-US-14
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как любой авторизованный пользователь, я хочу искать в базе знаний своими словами, чтобы найти карточку знаний по смыслу, а не только по точному названию. (Must)
- acceptance: Meaningful query → relevant results or honest empty; whitespace-only query → inline «Введите запрос», no search executed.
- scope: knowledge, semantic search

## REQ-US-15
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как Data Analyst, я хочу отфильтровать выдачу под роль аналитика (SQL/BI/DQ), чтобы не тонуть в ML/RAG-материалах. (Must)
- acceptance: Analyst role filter → only analyst-tagged materials; clearing filter restores unrestricted results while keeping query text.
- scope: knowledge, Data Analyst filter

## REQ-US-16
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как Data Scientist, я хочу находить материалы по методам ML и экспериментам, чтобы готовить разбор и углублять практику. (Must)
- acceptance: DS search/filter with ML materials present → ML/experiment results openable; navigate result → material with expected title.
- scope: knowledge, Data Scientist

## REQ-US-17
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как Data Analyst, я хочу увидеть честный empty state, если по запросу нет аналитического контента, чтобы не принять ML-выдачу за релевантный ответ. (Should)
- acceptance: Analyst search with no matches → empty «ничего не нашли» without substituting irrelevant ML top; reset filters / refine query CTA works.
- scope: knowledge, empty state

## REQ-US-18
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как Data Scientist или сотрудник СВА, я хочу открыть список разборов, чтобы найти нужную встречу или публикацию. (Must)
- acceptance: With razbors present → list with name, date, status; empty → empty state with CTA (e.g. to voting).
- scope: razbory

## REQ-US-19
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как читатель разбора, я хочу читать longread с sticky TOC, чтобы навигировать по секциям метода и применения в аудите. (Must)
- acceptance: Published multi-section razbor → longread + TOC section jump; sticky TOC remains navigable in viewport on supported widths.
- scope: razbor, sticky TOC

## REQ-US-20
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как Data Scientist (автор контента), я хочу скачать или открыть `.ipynb` разбора, чтобы воспроизвести демонстрацию. (Must)
- acceptance: Attached notebook → download/open starts for matching file; missing `.ipynb` → download disabled/absent with clear caption, no false nbconvert promise.
- scope: razbor, notebook

## REQ-US-21
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как Data Scientist, я хочу видеть в разборе блок оценки качества (метрики), чтобы оценить пригодность метода для аудита. (Should)
- acceptance: Razbor with metrics → visible quality block with numeric/tabular metrics; intro/overview without metrics → explicit «обзор» type.
- scope: razbor, quality metrics

## REQ-US-22
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как админ (CDS / делегат), я хочу видеть shortlist кандидатов дайджеста (топ-5), чтобы утвердить состав недели. (Must)
- acceptance: Admin with formed shortlist → up to 5 ranked candidates; non-admin → HTTP 403; empty shortlist → empty «кандидатов нет» with refresh.
- scope: admin-digest, shortlist

## REQ-US-23
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как админ, я хочу явно включать и исключать материалы (Approve / Reject), чтобы контролировать, что уйдёт в рассылку. (Must)
- acceptance: Approve → included and persisted; Reject → excluded and reflected in UI (not silent checkbox).
- scope: admin-digest, Approve/Reject

## REQ-US-24
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как админ, я хочу видеть статус draft vs ready у кандидата, чтобы не отправить незавершённый материал. (Must)
- acceptance: Shortlist shows distinguishable draft/ready per row; send with included draft → blocked with message to remove/wait for ready.
- scope: admin-digest, draft/ready

## REQ-US-25
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как админ, я хочу открыть превью письма перед отправкой, чтобы проверить финальный вид дайджеста. (Must)
- acceptance: Preview with ≥1 ready selected → modal/page matching selection; preview service failure → error and send not considered verified.
- scope: admin-digest, email preview

## REQ-US-26
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как админ, я хочу понять, почему материал попал в shortlist (факторы скоринга), чтобы принять editorial-решение. (Should)
- acceptance: Candidate with score/factors → score and ≥2 readable factors; unavailable factors → «обоснование недоступно», no invented percentages.
- scope: admin-digest, scoring factors

## REQ-US-27
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как админ, я хочу массово отметить топ-N / select all, чтобы ускорить triage под дедлайн. (Nice)
- acceptance: Select-all / keep top-3 updates selection in one operation; manually clearing one item after batch keeps other selections.
- scope: admin-digest, batch selection

## REQ-US-28
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как рядовой сотрудник СВА, я хочу открыть прошлый выпуск в архиве, чтобы вернуться к материалам предыдущих недель. (Must)
- acceptance: Select past issue → period materials; empty archive → empty state with CTA to current issue.
- scope: archive

## REQ-US-29
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как читатель, я хочу пройти карточку с вопросами после материала или разбора, чтобы проверить понимание (после v1). (Nice / post-v1)
- acceptance: Published quiz card 5–10 questions → show score % and activity event if enabled; unpublished quiz → CTA hidden/disabled without broken link.
- scope: post-v1, quiz cards

## REQ-US-30
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как админ, я хочу управлять YAML-конфигами пайплайна в веб-UI, чтобы менять источники и правила без деплоя (расширение роли админа). (Nice / post-v1)
- acceptance: Valid YAML save → config active; invalid YAML → validation error by field/line, previous valid config remains; non-admin → HTTP 403.
- scope: post-v1, pipeline YAML config

## REQ-US-31
- source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md
- description: Как админ, я хочу отправить утверждённый еженедельный дайджест, чтобы доставить подборку сотрудникам СВА и зафиксировать выпуск в архиве. (Must)
- acceptance: Confirm send with ≥1 ready (preview policy if required) → initiate send, success UI, archive updated; repeat send → no uncontrolled duplicate / already-sent message or explicit re-send; network failure → error, not marked sent, selection preserved.
- scope: admin-digest, digest send, archive
