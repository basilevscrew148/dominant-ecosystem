import { readFileSync, writeFileSync, existsSync, appendFileSync } from 'node:fs'

const STATE_PATH = 'D:\\Knowledge\\dominant-state.json'
const JOURNAL_PATH = 'D:\\Knowledge\\dominant-journal.jsonl'

export const inject = ['tools', 'webServer', 'systemPrompt']

function readState() {
  if (!existsSync(STATE_PATH)) return { goal: '', chronotope: '', parking: [] }
  try {
    const s = JSON.parse(readFileSync(STATE_PATH, 'utf8'))
    return {
      goal: typeof s.goal === 'string' ? s.goal : '',
      chronotope: typeof s.chronotope === 'string' ? s.chronotope : '',
      parking: Array.isArray(s.parking) ? s.parking.filter((x) => typeof x === 'string') : [],
    }
  } catch {
    return { goal: '', chronotope: '', parking: [] }
  }
}

function writeState(s) {
  writeFileSync(STATE_PATH, JSON.stringify(s, null, 2), 'utf8')
  return s
}

function journal(action, sessionId, s) {
  try {
    appendFileSync(JOURNAL_PATH, JSON.stringify({ ts: new Date().toISOString(), action, sessionId, ...s }) + '\n', 'utf8')
  } catch {}
}

function readJournal(limit = 20) {
  if (!existsSync(JOURNAL_PATH)) return []
  try {
    return readFileSync(JOURNAL_PATH, 'utf8').trim().split('\n').filter(Boolean).slice(-limit).map((l) => { try { return JSON.parse(l) } catch { return null } }).filter(Boolean)
  } catch {
    return []
  }
}

const json = (v, status = 200) =>
  new Response(JSON.stringify(v, null, 2), { status, headers: { 'content-type': 'application/json; charset=utf-8' } })

const PAGE = `<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Доминанта</title>
<style>body{font-family:system-ui,Segoe UI,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem;color:#111;background:#fafafa}
h1{font-size:1.4rem}label{display:block;margin:1rem 0 .3rem;font-weight:600}
input,textarea{width:100%;box-sizing:border-box;padding:.5rem;font:inherit;border:1px solid #ccc;border-radius:6px}
button{padding:.5rem 1rem;border:0;border-radius:6px;cursor:pointer;background:#2563eb;color:#fff}
button.ghost{background:#ddd;color:#333}#status{color:#2563eb;min-height:1.2em}
#hist{font-family:monospace;font-size:.85rem;white-space:pre-wrap;background:#eee;padding:.6rem;border-radius:6px;margin-top:1rem}
</style></head><body>
<h1>Доминанта <small>(принцип А. А. Ухтомского)</small></h1>
<label>Цель (очаг)</label><textarea id="goal" rows="2"></textarea>
<label>Хронотоп (целевое состояние)</label><textarea id="chronotope" rows="2"></textarea>
<label>Паркинг (по строке)</label><textarea id="parking" rows="4"></textarea>
<div style="margin-top:1rem"><button onclick="save()">Сохранить</button><button class="ghost" onclick="clearAll()">Сбросить</button><span id="status"></span></div>
<div id="hist"></div>
<script>
async function load(){const s=await (await fetch('/plugin/dominant/state')).json();
 document.getElementById('goal').value=s.goal||'';document.getElementById('chronotope').value=s.chronotope||'';
 document.getElementById('parking').value=(s.parking||[]).join('\\n');}
async function hist(){const h=await (await fetch('/plugin/dominant/history')).json();
 document.getElementById('hist').textContent=h.slice(-10).map(e=>(e.ts||'').slice(5,19)+' ['+e.action+'] '+(e.goal||'')).join('\\n');}
async function save(){const parking=document.getElementById('parking').value.split('\\n').map(x=>x.trim()).filter(Boolean);
 const body={goal:document.getElementById('goal').value,chronotope:document.getElementById('chronotope').value,parking};
 await fetch('/plugin/dominant/state',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
 document.getElementById('status').textContent='сохранено';setTimeout(()=>document.getElementById('status').textContent='',1500);hist();}
async function clearAll(){await fetch('/plugin/dominant/state',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({goal:'',chronotope:'',parking:[]})});load();hist();}
load();hist();
</script></body></html>`

export function apply(ctx) {
  ctx.effect(() =>
    ctx.tools.register({
      name: 'dominant',
      description:
        'Удерживает «доминанту» (принцип А. А. Ухтомского) как постоянное состояние: господствующая цель (goal), ' +
        'целевое состояние/горизонт (chronotope) и список отложенного (parking). action=get — прочитать; set — установить/обновить ' +
        '(пустые поля сохраняют прежние, parking заменяет список); clear — сбросить; history — журнал смен доминант. ' +
        'Состояние живёт в файле и переживает сессии.',
      parameters: {
        type: 'object',
        properties: {
          action: { type: 'string', enum: ['get', 'set', 'clear', 'history'], description: 'get/set/clear/history.' },
          goal: { type: 'string', description: 'Текущая доминанта (одно предложение).' },
          chronotope: { type: 'string', description: 'Целевое состояние: что будет верно, когда доминанта разрешится.' },
          parking: { type: 'array', items: { type: 'string' }, description: 'Список отложенного (сопряжённое торможение).' },
        },
        required: ['action'],
        additionalProperties: false,
      },
      output: {
        schema: {
          type: 'object',
          properties: { goal: { type: 'string' }, chronotope: { type: 'string' }, parking: { type: 'array', items: { type: 'string' } }, history: { type: 'array' } },
        },
        render: (_args, value) => [{ type: 'text', text: JSON.stringify(value, null, 2) }],
      },
      async execute(args, exec) {
        const a = args || {}
        const sid = String((exec && exec.agent && exec.agent.id) || 'global')
        if (a.action === 'clear') {
          const s = { goal: '', chronotope: '', parking: [] }
          journal('clear', sid, s)
          return writeState(s)
        }
        if (a.action === 'set') {
          const prev = readState()
          const s = {
            goal: typeof a.goal === 'string' ? a.goal : prev.goal,
            chronotope: typeof a.chronotope === 'string' ? a.chronotope : prev.chronotope,
            parking: Array.isArray(a.parking) ? a.parking.filter((x) => typeof x === 'string') : prev.parking,
          }
          journal('set', sid, s)
          return writeState(s)
        }
        if (a.action === 'history') return { history: readJournal(20) }
        return readState()
      },
    }),
  )

  ctx.effect(() =>
    ctx.webServer.register({
      kind: 'exact',
      path: '/plugin/dominant/state',
      resource: async (request) => {
        if (request.method === 'POST') {
          try {
            const body = await request.json()
            const s = {
              goal: typeof body.goal === 'string' ? body.goal : '',
              chronotope: typeof body.chronotope === 'string' ? body.chronotope : '',
              parking: Array.isArray(body.parking) ? body.parking.filter((x) => typeof x === 'string') : [],
            }
            journal('set', 'page', s)
            return json(writeState(s))
          } catch {
            return json(readState())
          }
        }
        return json(readState())
      },
    }),
  )

  ctx.effect(() =>
    ctx.webServer.register({ kind: 'exact', path: '/plugin/dominant/history', resource: async () => json(readJournal(50)) }),
  )

  ctx.effect(() =>
    ctx.webServer.register({ kind: 'exact', path: '/plugin/dominant', resource: async () => new Response(PAGE, { headers: { 'content-type': 'text/html; charset=utf-8' } }) }),
  )

  ctx.effect(() =>
    ctx.systemPrompt.section({
      name: 'dominant',
      order: 900,
      text: () => {
        const s = readState()
        return s.goal ? `Текущая доминанта (принцип Ухтомского): ${s.goal}` : ''
      },
    }),
  )
}
