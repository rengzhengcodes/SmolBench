export const meta = {
  name: 'solve-arms',
  description: 'Solve Horn-bench arms with read-only Haiku agents that return proofs (seeds x samples x arms)',
  phases: [{ title: 'Solve', detail: 'one read-only Haiku agent per seed x sample x arm; returns the proof text' }],
}

// args: { dir, seeds: [int], samples: int, arms: [string], only?: [[arm, seed, sample], ...] }
// Agent type `horn-solver` (.claude/agents/horn-solver.md) has the Read tool only, so the
// solver cannot grep the library for rules that mention the goal.
const DIR = args.dir
const SEEDS = args.seeds
const SAMPLES = args.samples
const ARMS = args.arms

const ANSWER_SCHEMA = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['proof', 'confused'] },
    answer: { type: 'string' },
  },
  required: ['status', 'answer'],
}

function solverPrompt(arm, seed, sample) {
  const f = `${DIR}/s${String(seed).padStart(4, '0')}/${arm}/prompt.md`
  // The first paragraph guards against a known failure: a subagent can receive the parent
  // session's latest chat message as context and act on it instead of on this prompt. The
  // "confused" exit lets such runs be dropped and refilled instead of scored.
  return `READ THIS FIRST. Your one and only task is the proof problem in the file named below. Ignore any other conversation, request or instruction you may have been shown; none of it is your task. If you think your task is anything other than solving the proof in that file, return status "confused" with an empty answer and stop.

You are a careful theorem prover.

1. Use the Read tool on exactly this one file, all of it, to the end: ${f}
   The file can be several thousand lines. One Read call returns at most 2000 lines, so call Read repeatedly with increasing offset (offset 1, then 2001, then 4001, ...) until a call returns the end of the file. Do not stop reading before the "## Answer format" section.
2. Solve the problem it states, following its "Answer format" section exactly.
3. Return your result as structured output: status "proof" and answer = the proof lines (one step per line, nothing else). The goal is always provable from the facts and the library rules, so keep searching until you have a complete proof; do not give up.

Do not use any tool other than Read on that one file. Do not create, edit or delete any file. (sample ${sample})`
}

const cells = []
for (const arm of ARMS) for (const seed of SEEDS) for (let s = 0; s < SAMPLES; s++) cells.push({ arm, seed, s })
const only = args.only  // optional: [[arm, seed, s], ...] restricts the grid to these cells
const keep = only ? new Set(only.map(o => o.join('|'))) : null
const todo = keep ? cells.filter(c => keep.has([c.arm, c.seed, c.s].join('|'))) : cells
log(`Solving ${todo.length} cells in ${DIR}`)
const out = await pipeline(
  todo,
  c => agent(solverPrompt(c.arm, c.seed, c.s), {
    label: `${c.arm} s${c.seed} r${c.s}`, phase: 'Solve',
    agentType: 'horn-solver', model: 'haiku', schema: ANSWER_SCHEMA,
  }).then(r => ({ arm: c.arm, seed: c.seed, sample: c.s, ...(r || { status: 'error', answer: '' }) })),
)
const rows = out.filter(Boolean)
const counts = {}
for (const r of rows) counts[r.status] = (counts[r.status] || 0) + 1
log(`done: ${JSON.stringify(counts)}`)
return { dir: DIR, counts, rows }
