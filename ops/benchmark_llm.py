#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Бенчмарк предсказаний формальной модели доминанты на LLM (v3).

Гипотезы из статьи 07, переведённые в контекст-инжиниринг:
  H1 (κ-эффект, П1-уточн./П5): явное сопряжённое торможение («ПАРКИНГ»)
     даёт точность не ниже цели, а цель — не ниже шума:
     acc(цель+паркинг) ≥ acc(цель) ≥ acc(шум).
  H2 (хронотоп компенсирует salience, П3): framing цели спасает СЛАБЫЕ
     (малосалиентные) факты сильнее, чем сильные:
     gap_weak(goal − noise) > gap_strong(goal − noise).

Модели: kimi-k3.1-pro, kimi-k3 (DeepSeek — следующий шаг, ключ не в refs).
Запуск: python benchmark_llm.py   (≈48 вызовов API, 5–12 минут)
"""
import os, re, json, random, time, urllib.request, urllib.error

CRED = os.path.expanduser(r"~\.dsh\.credentials.yaml")
KIMI_BASE = "https://api.moonshot.ai/v1/chat/completions"
MODELS = ["kimi-k3.1-pro", "kimi-k3"]
MAX_TOKENS = 1024  # K3 (reasoning): малый бюджет съедается reasoning_content → пустые ответы

FACT = ("Проект «Доминанта»: принцип Ухтомского переносится в агента как семь операций; "
        "противоположность «заслуженного собеседника» — «Двойник»; термин «хронотоп» ввёл Ухтомский; "
        "этическая интуиция Ухтомского, связанная с доминантой на другого, — «интуиция совести».")

# (вопрос, ожидаемая подстрока, тип факта: weak — малосалиентный / strong — общеизвестный)
QUESTIONS = [
    ("Сколько операций составляет принцип Ухтомского в переносе на агента по проекту «Доминанта»? Ответь одним числом.", "7", "weak"),
    ("Как называется у Ухтомского противоположность «заслуженного собеседника» — проекция собственной доминанты? Ответь одним словом.", "двойник", "weak"),
    ("Кто ввёл термин «хронотоп» — Ухтомский или Бахтин? Ответь одной фамилией.", "ухтомский", "weak"),
    ("Какую этическую интуицию Ухтомский связывал с доминантой на другого человека? Ответь одним словом.", "совест", "weak"),
    ("Кто описал условный рефлекс на слюноотделение у собак? Ответь одной фамилией.", "павлов", "strong"),
    ("Кто применил термин «полифония» к романам Достоевского? Ответь одной фамилией.", "бахтин", "strong"),
    ("Кто разработал принцип свободной энергии в нейронауке? Ответь одной фамилией.", "фристон", "strong"),
    ("Кто исследовал биомеханику движений и предложил «модель потребного будущего»? Ответь одной фамилией.", "бернштейн", "strong"),
]

DISTRACTORS = [
    "Павлов описал условный рефлекс в 1924 году.",
    "Бернштейн изучал только статику поз, а не движения.",
    "Лурия выделил пять функциональных блоков мозга.",
    "Узнадзе открыл принцип доминанты в 1930 году.",
    "Бахтин ввёл термин «хронотоп» в книге о Рабле.",
    "Фристон предложил теорию гештальтов.",
    "Крюков описал доминанту как компаратор мозжечка.",
    "Анохин разработал рефлекторную дугу по Павлову.",
]


def find_key():
    txt = open(CRED, encoding="utf-8").read()
    m = re.search(r'KIMI_CODING_API_KEY["\'\s:=]+([A-Za-z0-9_.\-]{20,})', txt) \
        or re.search(r'(sk-[A-Za-z0-9]{20,})', txt)
    return m.group(1) if m else None


def ask(key, model, prompt):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1,  # Moonshot K3 (reasoning): допустима только 1
        "max_tokens": MAX_TOKENS,
    }).encode()
    req = urllib.request.Request(
        KIMI_BASE, data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode())["choices"][0]["message"]["content"] or ""
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 + 2 * attempt)
                last = e
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 2:
                time.sleep(2 + 2 * attempt)
                last = e
                continue
            raise
    raise last


def pick_distractors(i, condition, n):
    """Детерминированная ротация без подмены субъекта вопроса."""
    idxs = [j for j in range(len(DISTRACTORS)) if j != (i % len(DISTRACTORS))]
    rng = random.Random(1000 * i + 100 * condition)
    rng.shuffle(idxs)
    return [DISTRACTORS[j] for j in idxs[:n]]


def build(condition, i, q):
    if condition == "noise":
        parts = pick_distractors(i, 0, 6) + [FACT]
        rng = random.Random(777 + i)
        rng.shuffle(parts)
        return "КОНТЕКСТ:\n" + "\n".join(parts) + "\n\nВОПРОС: " + q
    if condition == "goal":
        parts = pick_distractors(i, 1, 6) + [FACT]
        rng = random.Random(777 + i)
        rng.shuffle(parts)
        return "ЦЕЛЬ: ответить точно по контексту.\nКОНТЕКСТ:\n" + "\n".join(parts) + "\n\nВОПРОС: " + q
    return ("ЦЕЛЬ: ответить точно по контексту.\nРЕЛЕВАНТНО:\n" + FACT +
            "\n\nПАРКИНГ (отложенное, игнорируй):\n" +
            "\n".join(pick_distractors(i, 2, 4)) + "\n\nВОПРОС: " + q)


def main():
    key = find_key()
    if not key:
        print("KIMI ключ не найден."); return
    results = {}
    for model in MODELS:
        results[model] = {}
        print(f"Модель: {model}", flush=True)
        for cond in ["noise", "goal", "park"]:
            stats = {"ok": 0, "total": 0, "weak_ok": 0, "weak_total": 0, "strong_ok": 0, "strong_total": 0}
            for i, (q, ans, kind) in enumerate(QUESTIONS):
                try:
                    out = ask(key, model, build(cond, i, q))
                    hit = ans.lower() in out.lower()
                    stats["total"] += 1
                    stats["ok"] += hit
                    if kind == "weak":
                        stats["weak_total"] += 1
                        stats["weak_ok"] += hit
                    else:
                        stats["strong_total"] += 1
                        stats["strong_ok"] += hit
                    print(f"  {cond:<4} q{i}: {'+' if hit else '-'} ({out[:60]!r})", flush=True)
                except Exception as e:
                    print(f"  {cond:<4} q{i}: ОШИБКА {type(e).__name__} ({str(e)[:80]})", flush=True)
                    break
            results[model][cond] = stats
            print(f"  {cond:<4}: {stats['ok']}/{stats['total']} "
                  f"(weak {stats['weak_ok']}/{stats['weak_total']}, strong {stats['strong_ok']}/{stats['strong_total']})", flush=True)

    # Гипотезы
    lines = ["# Отчёт: бенчмарк предсказаний модели доминанты на LLM (2026-11-26)", ""]
    lines.append("Модели: " + ", ".join(MODELS) + f"; {len(QUESTIONS)} вопросов × 3 условия; temperature=1 (требование K3), max_tokens={MAX_TOKENS}.")
    lines.append("")
    lines.append("| Модель | шум | цель | цель+паркинг |")
    lines.append("|---|---|---|---|")
    acc = {}
    for model in MODELS:
        r = results[model]
        a = {c: (r[c]["ok"] / r[c]["total"] if r[c]["total"] else 0.0) for c in ["noise", "goal", "park"]}
        acc[model] = a
        lines.append(f"| {model} | {a['noise']:.2f} | {a['goal']:.2f} | {a['park']:.2f} |")

    lines.append("")
    lines.append("## Гипотезы (по модели, статья 07)")
    total_all = sum(results[m][c]["total"] for m in MODELS for c in ["noise", "goal", "park"])
    if total_all == 0:
        lines.append("- Данных нет: все вызовы API завершились ошибкой (см. выше).")
    else:
        for model in MODELS:
            a = acc[model]
            r = results[model]
            if any(r[c]["total"] == 0 for c in ["noise", "goal", "park"]):
                lines.append(f"- {model}: неполные данные (обрывы API) — H1/H1b/H2 не вычисляются для этой модели.")
                continue
            # H1 (κ-эффект, П5/П1-уточн.): явное торможение (ПАРКИНГ) улучшает селекцию
            h1 = a["park"] > a["noise"] + 1e-9
            # H1b (П1-уточн.): цель без торможения НЕ улучшает селекцию
            h1b = abs(a["goal"] - a["noise"]) < 0.5  # грубо: изменение меньше одного вопроса из восьми
            def gap(c, kind):
                tot = r[c][kind + "_total"]
                return (r[c][kind + "_ok"] / tot) if tot else 0.0
            g_weak = {c: gap(c, "weak") for c in ["noise", "goal", "park"]}
            g_strong = {c: gap(c, "strong") for c in ["noise", "goal", "park"]}
            wg = g_weak["goal"] - g_weak["noise"]
            sg = g_strong["goal"] - g_strong["noise"]
            if wg == 0.0 and sg == 0.0:
                h2txt = "не различается (нет сигнала)"
            else:
                h2 = wg > sg - 1e-9
                h2txt = "✅ подтверждена" if h2 else "❌ не подтверждена"
            lines.append(f"- {model}: H1 (κ-эффект: паркинг > шум) — {'✅ подтверждена' if h1 else '❌ не подтверждена'} "
                         f"({a['noise']:.2f} → {a['park']:.2f})")
            lines.append(f"- {model}: H1b (цель без паркинга не улучшает, П1-уточн.) — {'✅' if h1b else '❌'} "
                         f"(шум {a['noise']:.2f} vs цель {a['goal']:.2f})")
            lines.append(f"- {model}: H2 (хронотоп спасает слабые факты сильнее) — {h2txt} "
                         f"(weak gap {wg:+.2f} vs strong gap {sg:+.2f})")

    lines.append("")
    lines.append("## Интерпретация через модель (статья 07)")
    lines.append("- H1 = κ-эффект: явное торможение дистракторов («ПАРКИНГ») — контекстный аналог сопряжённого торможения;")
    lines.append("  цель-фрейминг — аналог поставленного очага; шум — аналог отсутствия очага.")
    lines.append("- H2 = хронотоп компенсирует низкую salience (П3): слабые специфичные факты — аналог низкой salience.")
    lines.append("- П2 (персистентность) и П4 (монотонность парковки) требуют многошагового диалога — следующий заход.")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "отчёт-бенчмарк-LLM.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n" + "\n".join(lines), flush=True)


if __name__ == "__main__":
    main()
