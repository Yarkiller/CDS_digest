Write a Russian longread for СВА readers from the transcript below.
Use only what the transcript says; do not add facts, names, numbers, tools or versions that are not in it.

- Name every level-2 section after a real topic of the talk, with no fixed count and no padding; do not merge unrelated topics.
- When the talk has no named chapters, split it into the implicit editorial chapters an experienced editor would write, and name each by its topic in the speaker's terms.
- Structure the article as a single speaker's argument: sections follow the topics of the talk.
- Place optional sections wherever the argument needs them; do not force a fixed order.
- Mark key theses in **bold**. Give a memorable direct statement as a markdown blockquote.
- Do not open with a level-1 heading; the title is a separate JSON field.

## Конкретика

Include this section only when the transcript carries concrete names, numbers, tools or caveats worth keeping.
Prefer bullets in the `**item** — the caveat the speaker gave` shape. A table is allowed only when the talk itself presents an explicit grid of numbers.
Spell tool names canonically (PostgreSQL, not «постгрес») and never invent a version.
Omit the section entirely when there is nothing concrete — no placeholder and no apology.

## Зачем это СВА

Include this section only when the talk has a working analog for СВА — control, data, model, vendor, information security, process quality — even if the speaker never said «аудит».
Write one editorial paragraph in the edition's voice («Для СВА это значит…»).
Do not invent a duty, an internal standard or a number.
Omit the section when there is no such analog.

## Аудитория

Кто целевая аудитория материала? Верни JSON array ролей из: employee, analyst, ds.
