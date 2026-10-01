# Resource limits

- Run every browser launch, Electron/emulator, and command expected to exceed ~2 GiB through `~/.codex/bin/heavy-gate [-n N] -- <cmd>`, regardless of tool or hook detection. `-n` counts concurrent browsers; **2 slots are shared machine-wide** with Claude/OMP.
- Prefer serial browser verification and `--workers=1`; one browser per process, closed in `finally`. Keep browser batches ≤2 and include this policy in browser-capable subagents' prompts.
- Use `exec_command` with a short `yield_time_ms`, then poll with `write_stdin`. Let the gate wait; never wrap it in `timeout`. Never bypass the hook or isolation, override `HEAVY_GATE_*` for real workloads, or add per-project locks.
- For script/package launches, use explicit `cd /absolute/project &&` or absolute script paths so the hook resolves them correctly.
- Before parallel heavy work, check `free -m` and `~/.codex/bin/heavy-gate --status`. Stop only your own scopes/processes; check for leftovers after SIGKILL.
- Guard other shared resources (ports, GPU, dev servers) with a lock or check at use time.

Consult `~/.codex/bin/README.md` for setup, troubleshooting, or gate/hook changes; run its regression checks after changes.
