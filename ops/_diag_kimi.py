import re, json, urllib.request, urllib.error

txt = open(r"C:\Users\basil\.dsh\.credentials.yaml", encoding="utf-8").read()
m = re.search(r'KIMI_CODING_API_KEY["\'\s:=]+([A-Za-z0-9_.\-]{20,})', txt) or re.search(r'(sk-[A-Za-z0-9]{20,})', txt)
key = m.group(1) if m else None
print("key prefix:", (key[:8] + "... len " + str(len(key))) if key else None)

body = json.dumps({
    "model": "kimi-k3.1-pro",
    "messages": [{"role": "user", "content": "Привет, ответь одним словом."}],
    "temperature": 0,
    "max_tokens": 256,
}).encode()
req = urllib.request.Request(
    "https://api.moonshot.ai/v1/chat/completions", data=body,
    headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print("OK", r.status)
        print(r.read().decode()[:400])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode()[:600])
