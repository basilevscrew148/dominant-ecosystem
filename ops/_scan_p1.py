#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скан параметров для П1: ищем режим, где латентность захвата
строго не возрастает с α и различает хотя бы два значения.
Динамика — точный порт dominant-rs::step (шум=0)."""
import math

def tanh(x): return math.tanh(x)

def leader(x): return max(range(len(x)), key=lambda i: x[i])

def dominant(x, thr=0.5, gap=0.2):
    order = sorted(range(len(x)), key=lambda i: -x[i])
    l, r = order[0], order[1]
    if x[l] >= thr and x[l] - x[r] >= gap:
        return l
    return None

def step(x, p, goal, s, g):
    l = leader(x)
    prec = [p["p0"] + p["a"] * max(v, 0.0) for v in x]
    nxt = []
    for i in range(len(x)):
        boost = (1.0 + g[i]) if i == goal else 1.0
        inhib = p["k"] * max(x[l], 0.0) if i != l else 0.0
        inp = prec[i] * s[i] * boost
        nxt.append(tanh(p["rho"] * x[i] + p["w"] * max(x[i], 0.0) + inp - inhib))
    return nxt

def capture(p, goal, s, g, x0, steps=100):
    x = list(x0)
    for t in range(steps):
        x = step(x, p, goal, s, g)
        if dominant(x) == goal:
            return t
    return steps

base = dict(p0=1.0, a=0.0, rho=0.8, w=0.2, k=0.35)
found = []
for s_goal in [0.14, 0.16, 0.18, 0.20, 0.22, 0.24]:
    for s_comp in [0.30, 0.35, 0.40, 0.45, 0.50]:
        for k in [0.35, 0.5, 0.6]:
            for x0v in [0.0, 0.1, 0.2]:
                caps = []
                for a in [0.0, 0.4, 0.8, 1.2]:
                    p = dict(base, a=a, k=k)
                    caps.append(capture(p, 0, [s_goal, s_comp, 0.10, 0.10], [1.0, 0.0, 0.0, 0.0], [x0v, 0, 0, 0]))
                distinct = len(set(caps)) >= 2
                monotone = all(b <= c for b, c in zip(caps, caps[1:]))
                all_cap = all(c < 100 for c in caps)
                if distinct and monotone and all_cap:
                    found.append((caps, s_goal, s_comp, k, x0v))
                    print(f"caps={caps} s_goal={s_goal} s_comp={s_comp} k={k} x0={x0v}")

print("\nТакже: режим слабого k=0.35 (находка про симметричный precision):")
for s_goal, s_comp in [(0.16, 0.30)]:
    caps = []
    for a in [0.0, 0.4, 0.8, 1.2]:
        p = dict(base, a=a, k=0.35)
        caps.append(capture(p, 0, [s_goal, s_comp, 0.12, 0.10], [1.0, 0.0, 0.0, 0.0], [0.0, 0, 0, 0]))
    print(f"s_goal={s_goal} s_comp={s_comp} k=0.35 x0=0 -> caps={caps}")
print(f"\nНайдено режимов: {len(found)}")
