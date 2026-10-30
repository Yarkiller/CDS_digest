Write a Russian longread for СВА readers from the transcript below.
Ground every claim about the talk in the transcript. You may add textbook definitions of hard terms the speaker used, short parenthetical footnotes in the sentence («Редакционное примечание: …»), not [^n] endnotes, and reference data that make a figure or claim readable; never invent a version, name or number the speaker stated, and never present added context as the speaker's words.

- Name every level-2 section after a real topic of the talk, with no fixed count and no padding; do not merge unrelated topics.
- When the talk has no named chapters, split it into the implicit editorial chapters an experienced editor would write, and name each by its topic in the speaker's terms.
- Structure the article as a single speaker's argument: sections follow the topics of the talk.
- Place optional sections wherever the argument needs them; do not force a fixed order.
- Mark key theses in **bold**. Give a memorable direct statement as a markdown blockquote.
- Do not open with a level-1 heading; the title is a separate JSON field.

## Конкретика

Include this section only when the talk carries a name, number, tool or caveat a СВА reader would stop on.
Keep only interesting or explanatory facts — a number that changes how the reader understands the talk. Skip a static inventory of layer sizes, counts or labels that do not explain themselves.
Prefer bullets in the `**item** — why this number or name matters` shape. A table is allowed only when the talk itself presents an explicit grid of numbers.
Spell tool names canonically (PostgreSQL, not «постгрес») and never invent a version.
You may add a short definition, footnote or reference figure so the fact is readable; mark it as editorial, not as the speaker's words.
Omit the section entirely when there is nothing worth keeping — no placeholder and no apology.

## Зачем это СВА

Include this section only when the talk has a working analog for СВА — control, data, model, vendor, information security, process quality — even if the speaker never said «аудит».
Write one editorial paragraph in the edition's voice («Для СВА это значит…»).
Do not invent a duty, an internal standard or a number.
Omit the section when there is no such analog.

## Аудитория

Кто целевая аудитория материала? Верни JSON array ролей из: employee, analyst, ds.
