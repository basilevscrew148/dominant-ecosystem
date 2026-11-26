---
title: "Prior-art обзор (GitHub API): кто уже кодирует метод мыслителя как логику"
type: article
created: "2026-11-25"
tags: ["prior-art", "github", "dominant", "agent-skills"]
source: github-api
---

# Prior-art обзор (GitHub API, систематический)

> Систематическая проверка: делал ли кто на GitHub «инструмент/плагин, где метод мыслителя — базовая логика», и в частности — доминанту Ухтомского. Метод: GitHub Search API (`/search/repositories`), ключевые запросы; результат — по состоянию на 2026-11-25.

## 1. Прямая реализация доминанты — НАЙДЕНА (важная поправка)

**`metabolicrussianai/metabolic_russian_ai`** — [github.com/metabolicrussianai/metabolic_russian_ai](https://github.com/metabolicrussianai/metabolic_russian_ai)

> «A neurophysiological runtime for agent behaviour. No backprop, no loss, no RLHF — built on 160 years of Russian neurophysiology (Sechenov → Pavlov → **Ukhtomsky** → Bernstein → Luria → N. P. Bekhtereva). Public obfuscated demo. NDA on request.»

- 2 звезды, создан 2026-04, язык Python, **обфусцированная публичная демо + NDA**.
- Это **прямой prior art**: кто-то уже строит агентную среду на русской нейрофизиологии, включая Ухтомского.

**Поправка к прежнему выводу**: ниша не «пустая», а **с одним зачаточным игроком**. Что остаётся новым у экосистемы «Доминанта»:
- **открытость** (без обфускации/NDA);
- **этико-диалогическое измерение** (собеседник/Двойник — у конкурента нет);
- **холистическая экосистема** (теория + скиллы + промпты + книга), а не только рантайм;
- **7-операционный протокол** как явный, переносимый интерфейс.

## 2. Паттерн «метод → скилл агента» — зрелый и массовый

Запрос `six thinking hats skill` дал **19 репозиториев**. Репрезентативные:

| Репозиторий | Что делает | Звёзды |
|---|---|---|
| [bjcoombs/ai-native-toolkit](https://github.com/bjcoombs/ai-native-toolkit) | Claude Code plugin + скиллы: `/huddle` (Six Thinking Hats), `/assess`, `/deslop`, `/skill-forge` | 34 |
| [fabiolalli/aits-agents](https://github.com/fabiolalli/aits-agents) | AITS: 11-агентный фреймворк решений, выросший из «шести шляп», детерминированный движок | 14 |
| [juanallo/six-hats-skill](https://github.com/juanallo/six-hats-skill) | скилл шести шляп для AI-агента | — |
| [micheleceo/six-hats-plus-skill](https://github.com/micheleceo/six-hats-plus-skill) | шесть шляп + седьмая «Мудрец» | — |
| [Dihanzhang/think-with-me](https://github.com/Dihanzhang/think-with-me) | сократический партнёр: окно Джохари + шесть шляп | — |

Вывод: **кодирование метода мышления (де Боно) как скилла/плагина — устоявшийся, растущий паттерн** (топики: agent-skills, six-thinking-hats, claude-code-plugin). Экосистема «Доминанта» стоит в этом же мейнстриме, но с методом Ухтомского.

## 3. Луман → Zettelkasten → Obsidian (классика паттерна)

- [PKM-er/obsidian-zettelkasten-navigation](https://github.com/PKM-er/obsidian-zettelkasten-navigation)
- [Dyldog/luhman-obsidian-plugin](https://github.com/Dyldog/luhman-obsidian-plugin)

Метод Лумана (Zettelkasten) — **канонический случай** «метод мыслителя → инструмент»: нумерация, навигация, индексы как код.

## 4. Автономное исследование как инструмент

- [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) — агент глубокого поиска с цитатами (research-pipeline как продукт).

## 5. Дополнение (второй заход по GitHub API)

- **Анохин как агентная логика**: [StevenAlber/meta-arch](https://github.com/StevenAlber/meta-arch) — «reflexive cognitive architecture… integrating **Anokhin's Functional Systems Theory**, computational reflection, and Quantitative Type Theory»; [qqewq/GRA-Health-Swarm](https://github.com/qqewq/GRA-Health-Swarm) — рой, координируемый «акцептором результата действия» (АРД) Анохина.
- **«chronotope Bakhtin» → 0 репозиториев**: линия «хронотоп→инструмент» на GitHub пуста — свободная ниша для экосистемы «Доминанта».

## 6. Дополнение (третий заход, 2026-11-26: `dominant+attention`, `attention protocol`, `focus agent`, `interlocutor agent`)

- **`dominant attention agent` → 1 результат**, не релевантный (TopK-TarMAC — MARL-коммуникации). Прямой «доминанты Ухтомского» по-прежнему нет.
- **`attention protocol` → 151**, всё нерелевантно (W3C-отчёты, NNTP-клиенты). Ниша «протокол внимания как интерфейс агента» пуста.
- **`focus agent` → 7950** (шум; релевантные сверху — инфраструктура, не метод):
  - [nearai/ironclaw](https://github.com/nearai/ironclaw) — Agent OS (Rust, 12,7k★): приватность/безопасность, не внимание;
  - [katanemo/plano](https://github.com/katanemo/plano) — Rust LLM-proxy (7,1k★);
  - [HughYau/qiushi-skill](https://github.com/HughYau/qiushi-skill) — «求是Skill»: философия (диалектика) как 9 методов агента — **ближайший паттерн-сосед**: «главное противоречие» ≈ доминанта, «проверка практикой» ≈ разрешение;
  - [NeoLabHQ/context-engineering-kit](https://github.com/NeoLabHQ/context-engineering-kit) — скиллы качества агента (1,9k★).
- **`interlocutor agent` → 8**, из них содержательные:
  - [stefantax/socrates](https://github.com/stefantax/socrates) — сократический агент, рефлексирует процесс обучения собеседника;
  - [AshritVerma/gadfly-v3-public](https://github.com/AshritVerma/gadfly-v3-public) — сократический собеседник для живых занятий (voice-first);
  - [Kobayashi-Lab-at-APU/dividual-agent-slud2026](https://github.com/Kobayashi-Lab-at-APU/dividual-agent-slud2026) — SLUD 2026: стили речи под конкретного собеседника (dividual-агент);
  - [yagobski/interlocutor-effect](https://github.com/yagobski/interlocutor-effect) — EuroS&PW 2026: агент-собеседник вызывает до +23 п.п. утечки PII — **важное предупреждение для `sobesednik`**;
  - [Nickatak/pocket_claude](https://github.com/Nickatak/pocket_claude) — «карманный собеседник» для thinking-out-loud.
- **Уточнение вывода**: операция «собеседник» (№6) на GitHub уже представлена сократическими и персонализированными вариантами, но **без связи с доминантой/хронотопом**; операция «хронотоп Бахтина→инструмент» по-прежнему 0. Ухтомский как *цельный* 7-операционный протокол остаётся незанятым.

## Выводы

1. **Прямой Ухтомский prior art есть** (metabolic_russian_ai), но зачаточный, закрытый, без этико-диалогического слоя.
2. **Паттерн «метод → скилл/плагин» — мейнстрим** (де Боно: 19 репо; Луман: плагины Obsidian; исследование: gpt-researcher).
3. **Новизна экосистемы «Доминанта»** — не паттерн, а: (а) метод Ухтомского (доминанта + собеседник + хронотоп) как *единый* 7-операционный протокол; (б) открытая, холистическая упаковка (теория+скиллы+промпты+книга); (в) этико-диалогическая операция «собеседник» как инструмент.

*Ограничение:* поиск — по репозиториям (не по коду внутри репо); «не найдено» ≠ «не существует». Отрицательные выводы предварительны.
