#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Мини-симуляция доминанты: self-excitation (инерция) + латеральное торможение (сопряжённое торможение)
показывает, что господствующий очаг (а) побеждает, (б) тормозит конкурентов, (в) переживает снятие стимула."""
import numpy as np

def simulate():
    N = 5
    dt = 0.1
    steps = 1200
    x = np.zeros(N)
    self_w = 1.2      # само-возбуждение (>=1 -> бистабильность -> инерция)
    inhib = 0.35      # латеральное торможение -> сопряжённое торможение

    def signal(i, t):
        if i == 0 and 10 <= t <= 60:   # цель (очаг)
            return 1.5
        if i == 1 and 35 <= t <= 38:   # дистрактор
            return 1.3
        return 0.0

    trace = []
    for k in range(steps):
        t = k * dt
        s = np.array([signal(i, t) for i in range(N)])
        lateral = inhib * (x.sum() - x)          # торможение от остальных
        dx = -x + self_w * x + s - lateral
        x = np.clip(x + dt * dx, 0.0, 10.0)
        if k % 10 == 0:
            trace.append((round(t, 1), *(round(float(v), 2) for v in x)))

    print("Модель: dx/dt = -x + 1.2*x + s - 0.35*(сумма остальных)")
    print("Цель=узел0 (t 10-60), дистрактор=узел1 (t 35-38)\n")
    for t, *vals in trace[::30]:
        print(f"t={t:>5}: " + "  ".join(f"u{i}={v}" for i, v in enumerate(vals)))
    final = x
    print("\nИтог:")
    print(f"  активность очага u0 в конце        = {final[0]:.3f} (цель снята на t=60, держится -> инерция)")
    print(f"  активность дистрактора u1 в конце  = {final[1]:.3f} (подавлен -> сопряжённое торможение)")
    print(f"  остальные                          = {[round(v,3) for v in final[2:]]}")
    persisting = final[0] > 0.5
    inhibited = final[1] < 0.1
    print(f"\n  ВЕРДИКТ: инерция={'ДА' if persisting else 'НЕТ'}, торможение={'ДА' if inhibited else 'НЕТ'}")

if __name__ == '__main__':
    simulate()
