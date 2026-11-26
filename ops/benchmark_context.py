#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Бенчмарк v2: три условия (шум / только-цель / цель+паркинг) × N вопросов. Kimi (Moonshot)."""
import os, re, json, urllib.request

CRED = os.path.expanduser(r"~\.dsh\.credentials.yaml")
BASE = "https://api.moonshot.ai/v1/chat/completions"
MODELS = ["kimi-k3.1-pro", "kimi-k3"]

def find_key():
    try: txt = open(CRED, encoding='utf-8').read()
    except FileNotFoundError: return None
    m = re.search(r'KIMI_CODING_API_KEY["\'\s:=]+([A-Za-z0-9_.\-]{20,})', txt) or re.search(r'(sk-[A-Za-z0-9]{20,})', txt)
    return m.group(1) if m else None

def ask(key, model, prompt):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "max_tokens": 200}).encode()
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())["choices"][0]["message"]["content"]

QUESTIONS = [
    ("Сколько операций составляет принцип Ухтомского в переносе на агента (по проекту «Доминанта»)? Ответь одним числом.", "7"),
    ("Как называется у Ухтомского противоположность «заслуженного собеседника» (проекция собственной доминанты)?", "Двойник"),
]

def build(prompt_key, q, distractors):
    fact = "Проект «Доминанта»: принцип Ухтомского переносится в агента как семь операций; противоположность «заслуженного собеседника» — «Двойник»."
    if prompt_key == "noise":
        return "КОНТЕКСТ:\n" + "\n".join(distractors) + "\n" + fact + "\n\nВОПРОС: " + q
    if prompt_key == "goal":
        return "ЦЕЛЬ: ответить точно по контексту.\nКОНТЕКСТ:\n" + "\n".join(distractors) + "\n" + fact + "\n\nВОПРОС: " + q
    return ("ЦЕЛЬ: ответить точно по контексту.\nРЕЛЕВАНТНО:\n" + fact + "\n\nПАРКИНГ (отложенное, игнорируй):\n"
            + "\n".join(distractors[:4]) + "\n\nВОПРОС: " + q)

DISTRACTORS = [
    "Павлов описал условный рефлекс на слюноотделение в 1924 году.",
    "Бернштейн изучал биомеханику движений у пианистов.",
    "Лурия выделил три функциональных блока мозга.",
    "Узнадзе проводил опыты с тактильной иллюзией неравных шаров.",
    "Бахтин ввёл термин полифония для романов Достоевского.",
    "Фристон разработал принцип свободной энергии.",
    "Крюков моделировал компараторную функцию гиппокампа.",
    "Анохин описал афферентный синтез в функциональных системах.",
]

def main():
    key = find_key()
    if not key:
        print("KIMI ключ не найден — запустите вручную."); return
    print("Бенчмарк v2: 2 вопроса x 3 условия\n")
    for model in MODELS:
        print(f"Модель: {model}")
        for name, prompt_key in [("шум", "noise"), ("цель", "goal"), ("цель+паркинг", "goal+park")]:
            ok = 0; total = 0
            for q, ans in QUESTIONS:
                try:
                    out = ask(key, model, build(prompt_key, q, DISTRACTORS))
                    total += 1
                    if ans.lower() in out.lower(): ok += 1
                except Exception as e:
                    print(f"  {name}: ОШИБКА {type(e).__name__} ({str(e)[:60]})"); break
            if total: print(f"  {name:<12}: {ok}/{total}")
        print()
        break  # только первая доступная модель

if __name__ == '__main__':
    main()
