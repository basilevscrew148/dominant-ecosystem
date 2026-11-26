# Публикация экосистемы «Доминанта» на GitHub

Репозиторий подготовлен локально: git init выполнен, LICENSE добавлен, **первый коммит сделан (2026-11-26)**, `.gitignore` добавлен (`target/` исключён).

**Текущий блокер:** на этой машине нет авторизации GitHub — `gh auth status`: не залогинен; `GH_TOKEN`/`GITHUB_TOKEN` не заданы. Пуш невозможен без авторизации.

## 0. Авторизоваться (одно из двух)

```powershell
gh auth login          # интерактивно, через браузер
# или классический токен:
git remote add origin https://<токен>@github.com/<ваш-логин>/dominant-ecosystem.git
```

## 1. Создать удалённый репозиторий
На github.com: **New repository** → имя `dominant-ecosystem` (или своё) → без README (у нас свой). Либо: `gh repo create dominant-ecosystem --public --source=. --push` (сделает и репозиторий, и пуш).

## 2. Подключить и запушить

```powershell
cd "D:\Knowledge\Vault\90-Projects\доминанта-экосистема"
git remote add origin https://github.com/<ваш-логин>/dominant-ecosystem.git
git add -A
git commit -m "Экосистема «Доминанта»: теория, книга, скиллы, плагин, формальная модель"
git branch -M main
git push -u origin main
```

## 3. Что внутри (структура для читателя)

- `README-экосистема.md` — карта (это стартовая страница).
- `статьи/` — научная серия (6 статей + обзорная + prior-art).
- `книга/` — magnum opus (22 главы) + `Доминанта-книга.{epub,docx,pdf}`.
- `промпты/` — 5 переиспользуемых промптов.
- `plugin-dominant/` — DSH host-плагин `@local/dominant` (инструмент + страница + клиентский индикатор).
- `ops/` — симуляция доминанты (v1, v2) + бенчмарк контекст-инжиниринга + сборщики EPUB/DOCX.
- Скиллы (для копирования в `~/.dsh/skills/`): `dominant`, `sobesednik`, `chronotope-planner` — исходники см. в README.

## Почему это важно (против prior-art)

Прямой prior-art — `metabolicrussianai/metabolic_russian_ai` — **закрыт (обфускация + NDA)**. Этот репозиторий — открытый, холистический контур: теория → формализация → логика → инструменты → опыт, сквозь один инвариант (7 операций доминанты Ухтомского).
