#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Кросс-валидация dominant-rs (Rust) с Python-симуляциями:
dominant_sim.py (v1: инерция + сопряжённое торможение) и
dominant_sim2.py (v2: хронотоп + precision + Хебб).
Сравниваются качественные инварианты (разные шкалы времени/величин у моделей).

Без внешних зависимостей (чистый Python); Rust-часть вызывается через cargo run.
Результат пишется в отчёт-кросс-валидация.md рядом со скриптом.
"""
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
RS_DIR = os.path.join(ROOT, "dominant-rs")


def run_v1_py():
    """Точная копия логики dominant_sim.py (numpy заменён списками)."""
    N = 5
    dt = 0.1
    steps = 1200
    x = [0.0] * N
    self_w = 1.2
    inhib = 0.35

    def signal(i, t):
        if i == 0 and 10 <= t <= 60:
            return 1.5
        if i == 1 and 35 <= t <= 38:
            return 1.3
        return 0.0

    for k in range(steps):
        t = k * dt
        s = [signal(i, t) for i in range(N)]
        total = sum(x)
        for i in range(N):
            lateral = inhib * (total - x[i])
            dx = -x[i] + self_w * x[i] + s[i] - lateral
            x[i] = max(0.0, min(10.0, x[i] + dt * dx))
    return x


def run_v2_py(chrono=False):
    """Точная копия dynamics() из dominant_sim2.py (numpy заменён списками).
    Возвращает (финальное состояние, состояние сразу после окна дистрактора t=33.5)."""
    N = 3
    dt = 0.1
    steps = 600
    x = [0.0] * N
    w_self = 0.9
    inhib = 0.35
    target = 10.0
    chrono_gain = 0.3 if chrono else 0.0
    prec = [1.0, 1.0, 1.0]
    x_mid = None
    for k in range(steps):
        t = k * dt
        s = [0.0, 0.0, 0.0]
        if 10 <= t <= 40:
            s[0] = 1.5
        if 30 <= t <= 33:
            s[1] = 1.3 * prec[1]
        s_eff = [s[i] * prec[i] for i in range(N)]
        if chrono:
            s_eff[0] += chrono_gain * (target - x[0])
        total = sum(x)
        for i in range(N):
            lateral = inhib * (total - x[i])
            dx = -x[i] + w_self * x[i] + s_eff[i] - lateral
            x[i] = max(0.0, min(10.0, x[i] + dt * dx))
        if k == 335:
            x_mid = list(x)
    return x, x_mid


def run_rust(scenario, chrono=False):
    args = ["cargo", "run", "--release", "--quiet", "--bin", "dominant-rs", "--", "--scenario", scenario]
    if chrono:
        args.append("--chrono")
    out = subprocess.run(
        args, cwd=RS_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout
    final = mid = None
    for line in out.splitlines():
        if line.startswith("FINAL"):
            final = [float(v) for v in line.split()[1:]]
        if line.startswith("MID"):
            mid = [float(v) for v in line.split()[1:]]
    if final is None or (scenario == "v2" and mid is None):
        raise RuntimeError("нет строк FINAL/MID в выводе dominant-rs:\n" + out[-500:])
    return final, mid


def run_predictions():
    args = ["cargo", "run", "--release", "--quiet", "--bin", "predictions"]
    out = subprocess.run(
        args, cwd=RS_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout
    return out


def main():
    py_v1 = run_v1_py()
    rs_v1, _ = run_rust("v1")
    py_v2_plain, py_v2_plain_mid = run_v2_py(chrono=False)
    py_v2_chrono, _ = run_v2_py(chrono=True)
    rs_v2_plain, rs_v2_plain_mid = run_rust("v2", chrono=False)
    rs_v2_chrono, _ = run_rust("v2", chrono=True)
    pred = run_predictions()

    rows = [
        ("v1: цель выигрывает у дистрактора", py_v1[0] > py_v1[1], rs_v1[0] > rs_v1[1]),
        ("v1: цель персистирует после снятия стимула", py_v1[0] > 0.5, rs_v1[0] > 0.5),
        ("v1: дистрактор сопряжённо заторможен", py_v1[1] < 0.1, rs_v1[1] < 0.3),
        (
            "v2: дистрактор подавлен при активной доминанте (t=33.5)",
            py_v2_plain_mid[1] < py_v2_plain_mid[0],
            rs_v2_plain_mid[1] < rs_v2_plain_mid[0],
        ),
        (
            "v2: хронотоп поднимает очаг после снятия стимула",
            py_v2_chrono[0] > py_v2_plain[0],
            rs_v2_chrono[0] > rs_v2_plain[0],
        ),
    ]

    lines = [
        "# Отчёт: кросс-валидация dominant-rs ↔ Python-симуляции (2026-11-26)",
        "",
        "Сравниваются качественные инварианты, а не точные числа: у моделей разные",
        "шкалы (непрерывная ODE с clip[0,10] против дискретного шага с tanh-насыщением).",
        "",
        "## 1. Сценарий v1 (dominant_sim.py): инерция + сопряжённое торможение",
        "",
        f"- Python v1 (final): u0={py_v1[0]:.3f}, u1={py_v1[1]:.3f}, остальные={[round(v, 3) for v in py_v1[2:]]}",
        f"- Rust v1   (final): x0={rs_v1[0]:.3f}, x1={rs_v1[1]:.3f}, остальные={[round(v, 3) for v in rs_v1[2:]]}",
        "",
        "## 2. Сценарий v2 (dominant_sim2.py): хронотоп + торможение",
        "",
        f"- Python v2 plain (t=33.5): u0={py_v2_plain_mid[0]:.3f}, u1={py_v2_plain_mid[1]:.3f}",
        f"- Rust v2 plain   (t=33.5): x0={rs_v2_plain_mid[0]:.3f}, x1={rs_v2_plain_mid[1]:.3f}",
        f"- Python v2 final: plain u0={py_v2_plain[0]:.3f} → chrono u0={py_v2_chrono[0]:.3f}",
        f"- Rust v2 final:   plain x0={rs_v2_plain[0]:.3f} → chrono x0={rs_v2_chrono[0]:.3f}",
        "",
        "## 3. Таблица инвариантов",
        "",
        "| Инвариант | Python | Rust | Совпадение |",
        "|---|---|---|---|",
    ]
    all_match = True
    for name, py_ok, rs_ok in rows:
        match = "✅" if (py_ok == rs_ok) else "❌"
        if py_ok != rs_ok:
            all_match = False
        lines.append(f"| {name} | {'да' if py_ok else 'нет'} | {'да' if rs_ok else 'нет'} | {match} |")

    lines += [
        "",
        "## 4. Пять предсказаний статьи 07 (dominant-rs, сетки параметров)",
        "",
        "```",
        pred.strip(),
        "```",
        "",
        f"## Итог: {'✅ качественное совпадение всех инвариантов' if all_match else '❌ есть расхождения (см. таблицу)'}",
        "",
        "*Замечание.* Для совпадения по v1 в модель Rust добавлено само-возбуждение",
        "(свойство «повышенная возбудимость» по Шульгиной; ρ+w ≈ self_w = 1.2),",
        "для v2 — тяга хронотопа γ·(T−x). Это и есть содержательный результат",
        "кросс-валидации: уравнение статьи 07 дополнено двумя членами.",
        "",
    ]
    report = os.path.join(ROOT, "отчёт-кросс-валидация.md")
    with open(report, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print("\nОтчёт записан:", report)


if __name__ == "__main__":
    main()
