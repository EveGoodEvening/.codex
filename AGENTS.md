# AGENTS.md

## Project lessons

- When you learn something reusable while working in a project, record it in the `Lessons` section of the repo-level `AGENTS.md` at the repository root. This includes library versions, model names, project conventions, corrected assumptions, and fixes for mistakes. Do not write these lessons to the user-level global files under `~/.omp/agent/`.

## Network exposure

- Docker-published Compose ports can bypass expected UFW `deny incoming` behavior through Docker iptables chains; local/dev service ports should bind explicitly to `127.0.0.1` in `ports` mappings on cloud hosts unless public exposure is intended.

## Resource limits

- Run every browser launch, Electron/emulator, and command expected to exceed ~2 GiB through `~/.codex/bin/heavy-gate [-n N] -- <cmd>`, regardless of tool or hook detection. `-n` counts concurrent browsers; **2 slots are shared machine-wide** with Claude/OMP.
- Prefer serial browser verification and `--workers=1`; one browser per process, closed in `finally`. Keep browser batches ≤2 and include this policy in browser-capable subagents' prompts.
- Use `exec_command` with a short `yield_time_ms`, then poll with `write_stdin`. Let the gate wait; never wrap it in `timeout`. Never bypass the hook or isolation, override `HEAVY_GATE_*` for real workloads, or add per-project locks.
- For script/package launches, use explicit `cd /absolute/project &&` or absolute script paths so the hook resolves them correctly.
- Before parallel heavy work, check `free -m` and `~/.codex/bin/heavy-gate --status`. Stop only your own scopes/processes; check for leftovers after SIGKILL.
- Guard other shared resources (ports, GPU, dev servers) with a lock or check at use time.

Consult `~/.codex/bin/README.md` for setup, troubleshooting, or gate/hook changes; run its regression checks after changes.

## Lessons

- Codex has an independent `bin/heavy-gate` copy. Port containment fixes explicitly while keeping `/tmp/heavy-gate` locks shared with Claude/OMP; separate lock directories multiply the resource budget.
- Chromium can move its own PID into a sibling systemd scope through the host session bus. `MemoryMax` follows cgroup ancestry, not process ancestry. Keep `dbus-run-session` inside the limited scope and the supervisor on the host bus; host session services are intentionally isolated, and this is not a sandbox against deliberate same-user/root escape.
