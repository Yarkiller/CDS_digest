# Git: remote `origin`

По умолчанию удалённый репозиторий проекта — **`origin`** (Cursor Origin: `https://origin.cursor.com/yaroslav-chereshnev/digest-cds.git`).

## Правило для агентов

**Все git-операции с `origin`** (`push`, `pull`, `fetch`, `origin auth login` и т.п.) выполнять **только через WSL**, не из PowerShell/CMD.

На Windows аутентификация Cursor Origin из PowerShell часто падает (`Authentication failed`); в WSL credentials работают стабильно.

### Шаблон команд

Repo path в WSL (Windows `C:\Users\Yarkiller\PycharmPET-Projects\Digital_CDS`):

```bash
/mnt/c/Users/Yarkiller/PycharmPET-Projects/Digital_CDS
```

Обёртка для агента:

```powershell
wsl.exe -e bash -lc 'cd /mnt/c/Users/Yarkiller/PycharmPET-Projects/Digital_CDS && git <command>'
```

Примеры:

```powershell
wsl.exe -e bash -lc 'cd /mnt/c/Users/Yarkiller/PycharmPET-Projects/Digital_CDS && git status -sb'

wsl.exe -e bash -lc 'cd /mnt/c/Users/Yarkiller/PycharmPET-Projects/Digital_CDS && git push origin main'

wsl.exe -e bash -lc 'cd /mnt/c/Users/Yarkiller/PycharmPET-Projects/Digital_CDS && origin auth login'
```

### Локальные операции без origin

`git status`, `git diff`, `git add`, `git commit` (без push) можно выполнять из PowerShell — они не требуют Cursor Origin auth.

### Credentials

- Настраивать через `origin auth login` **в WSL**, не коммитить ключи в репозиторий.
- Не добавлять API keys в `.cursor/mcp.json`, `.env` или markdown-файлы правил.
- Папка `.cursor/` — локальная конфигурация IDE, в git не попадает.
