# F6: Critic-Candidates-Judge Loop

For diagrams with >15 shapes, single-pass generation often produces overlaps, missing edges, or off-grid placement that the validator catches but cannot fix. This loop adds an iterative refinement layer.

**Source:** *See it. Say it. Sorted.* — arxiv 2508.15222 (training-free agentic system, Critic VLM + multi-candidate LLMs + Judge VLM). The Skill adaptation uses Claude subagents in the same three roles.

**Feature flag:** `critic_judge_loop` — `off` / `on` / `auto` (default `auto` → on when shapes > 15).

## The four roles

| Role | What it does | Input | Output |
|---|---|---|---|
| **Critic** | Reads the current diagram + plan, lists 3–5 specific issues in priority order | `.drawio` + `.plan.json` + validator output | Plain-text issue list with cell-id references |
| **Candidate (×3)** | Each proposes an edited plan that fixes the Critic's issues, using a different strategy | Critic's issues + current plan | Three revised plans |
| **Judge** | Scores all three candidates against (a) plan-graph fidelity, (b) layout cleanliness, (c) the user's actual ask | Three plans + the original request | Picks one (with one-line justification) |
| **Renderer** | Emits the winning plan as `.drawio` XML | Winning plan | Final `.drawio` |

## Candidate strategies (deterministic prompts)

Each Candidate subagent gets the same input + a strategy directive. The strategies are intentionally different so the Judge has real choices:

- **Conservative** — minimal edits. Fix only what the Critic explicitly named. Don't reorganize.
- **Aggressive** — full restructure. Use a different layout pattern if it would fix more issues. Move shapes freely. Re-pick `vendor_icon` choices.
- **Focused** — fix the single highest-priority Critic issue completely; ignore the rest.

This is the exact diversity strategy named in the paper abstract: *"multiple candidate LLMs synthesize SVG updates with diverse strategies (conservative→aggressive, alternative, focused)."*

## Loop termination

| Stop when... | Why |
|---|---|
| Validator reports zero ERRORs **and** zero F2 quality warnings | Quality bar met |
| Three iterations completed | Diminishing returns |
| Same plan returned by all three Candidates | Converged |
| Judge picks the same plan two iterations in a row | Stable |

Three iterations is the soft cap; beyond that, the model usually starts trading one issue for another.

## Workflow in the Skill

The skill orchestrates this internally — no extra script. Sequence per iteration:

1. **Generate** initial `.drawio` + `.plan.json` (existing plan-then-emit workflow).
2. **Validate** — run `scripts/validate.py --features quality_gate=on,diagram_eval=on,grounding_manifest=on --mode strict`.
3. **If validation passes** → done.
4. **Critic pass** (one Claude subagent): produce a numbered issue list. Each issue cites cell ids and concrete coordinates.
5. **Candidates pass** (three subagents in parallel, one per strategy): each emits a revised `.plan.json`.
6. **Judge pass** (one subagent): pick the winner, justify in one sentence.
7. **Renderer**: emit `.drawio` from the winning plan.
8. **Goto 2** (max 3 iterations).

## Prompts (excerpt)

### Critic prompt template

```
You are the Critic. Read:
- {diagram.drawio}
- {plan.json}
- {validator-output.txt}

Output a numbered list of 3–5 specific, actionable issues. Each issue must:
- Cite the cell id(s) involved
- State the observable problem (overlap, missing edge, off-grid, wrong style, etc.)
- Be fixable by editing the plan JSON

Do NOT propose fixes — that's the Candidate's job. Do NOT list nits.

Order by impact. Stop at 5 issues.
```

### Candidate prompt template

```
You are Candidate-{conservative|aggressive|focused}. Strategy:
{strategy description from table above}

Read:
- {plan.json}
- Critic's issue list: {critic-output}

Emit a revised plan.json that addresses the issues per your strategy.
Preserve container hierarchy. Preserve `cite` fields (F3 grounding).
Output ONLY the JSON. No prose.
```

### Judge prompt template

```
You are the Judge. Read:
- Original user request: {user-message}
- Three candidate plans: A (conservative), B (aggressive), C (focused)
- Validator output for each: {a-validator, b-validator, c-validator}

Score each on:
1. plan-graph fidelity (does it preserve the source citations and node identities?)
2. layout cleanliness (validator quality_gate output — fewer crossings / better orthogonality?)
3. fit to the user's actual ask

Pick one. Output: "WINNER: {A|B|C}\nJUSTIFY: <one sentence>"
```

## When NOT to use the loop

- Small diagrams (<10 shapes) — single-pass usually suffices, loop is overkill
- Diagrams the user is actively editing in draw.io alongside generation — multiple Candidate plans confuse the working state
- Time-pressured client demos — loop adds 2–4× wall-clock latency

Set `critic_judge_loop: off` in SKILL.md frontmatter or pass `--features critic_judge_loop=off` to bypass.

## What this is NOT

It is **not** the agentic VLM loop from the paper (which used Gemini-2.5-Pro as a *vision* Critic against a *rendered* SVG). The Skill version is text-only: Critic reads the .drawio XML + validator output, not a rendered pixel image. This works for architecture diagrams because the validator already extracts the visual issues (overlaps, crossings, orthogonality) as text. For sketch-to-diagram (the paper's actual problem), a vision Critic would be necessary.

## Future enhancement

If the user wants the actual VLM loop (with a rendered PNG critique step):
1. Add `scripts/render-png.py` using draw.io desktop CLI: `draw.io -x -f png --width 1600 input.drawio output.png`
2. Pass the PNG to a Claude vision subagent as the Critic
3. Otherwise the workflow above is identical

Not implemented in v2.1 — keep the text-only loop for now.
