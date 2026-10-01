# Codex heavy-gate

Ported from `/root/.claude` commits `4464b3e`, `fdc25eb`, and `cd9c4ed`.
The gate keeps the same `/tmp/heavy-gate/slot-*` and `launch` locks as Claude/OMP:
**two slots total across clients, projects, sessions, and agents**, not two per client.
Prefer serial browser tests and `--workers=1`; reserve `-n 2` only for a command
that actually needs two concurrent browsers. This port preserves the source
policy's two-slot limit; it is not a strict one-browser global mutex.

Each launch requires at least 4500 MiB `MemAvailable`, is spaced by 20 seconds,
and runs in a user systemd scope with `MemoryMax=6G` and `MemorySwapMax=0` by
default. The gate keeps its slots until the scope and its descendants exit.
Unavailable systemd isolation refuses execution. This requires Linux, Bash,
`flock`, Python 3, and a working user systemd manager with memory controllers.

## Use

```sh
cd /absolute/project && ~/.codex/bin/heavy-gate -l project-e2e -- npx playwright test --workers=1
~/.codex/bin/heavy-gate --status
```

In Codex, use `exec_command` with `yield_time_ms: 1000` and poll its returned
`session_id` with `write_stdin`. A short yield is not a runtime deadline.
Do not add `timeout`, do not send work into an ungated interactive shell, and
do not override `HEAVY_GATE_*` for real workloads. When cancelling, stop only
your own gate PID or its reported scope; never clear shared locks or kill
another session's browser.

If calling through `functions.exec`, await the tool call and use
`functions.wait` only when that exec cell yields. Codex does not use Claude's
`run_in_background` parameter. Avoid shell tools whose execution deadlines
terminate queued work. When the hook rejects a launch, rerun it through the
gate. If isolation is unavailable, stop the workload instead of running uncapped.

Browser verification is one stage shared across projects, sessions, agents,
and loops. Before fanning out, check `free -m` and gate status. Prefer serial
verification or batches of at most two; give other workers static checks and
unit tests. Include the gate policy in every browser-capable subagent's prompt.
Launch one browser per process and close it in `finally`; do not add per-project
locks. Slots remain held until all scope descendants exit. After SIGKILL,
check for leftover processes belonging to your invocation.

## Activation

`AGENTS.md` is the global instruction file. `hooks.json` registers the
`PreToolUse` check. `[features] hooks = true` is included in the config template;
keep it enabled in the live `~/.codex/config.toml` too.

Codex requires trust for non-managed hooks. After a fresh checkout or a hook
definition change, open `/hooks` and review/trust **Checking browser memory
gate**. An enabled but untrusted hook is skipped. Trust is local state in
`config.toml`; do not commit path-specific trust hashes or use a blanket trust
bypass. Start a new Codex session after installation so global instructions
and hooks are loaded.

## Codex compatibility and limits

Verified against installed `codex-cli 0.159.3`, source tag `rust-v0.159.3`
(`01fc69f4026735edfdf6789820549727a4867b11`):

- `exec_command` is normalized to hook tool name `Bash` and
  `tool_input.command`, including calls through code mode. Match `^Bash$`.
- The supported denial is `hookSpecificOutput.permissionDecision = "deny"`
  with `hookEventName = "PreToolUse"` and a reason. Unsupported output fields
  such as `continue: false` can fail the hook without blocking execution.
- The hook receives the session/environment cwd, not the command's `workdir`
  override. For package scripts and relative launchers, put an explicit `cd`
  in the command or use absolute script paths.
- `write_stdin` does not invoke `PreToolUse` again. MCP/browser tools and
  dynamically constructed launches are not covered by this Bash matcher.
  The global instructions require these workloads to use the same gate.
  Use a gated shell launcher when a tool cannot participate in the shared gate;
  never launch a browser later through `write_stdin` into an ungated shell.
- The checker is best-effort launch detection, not a security sandbox or a
  browser counter. It scans CLI commands, runtime scripts/local imports,
  inline code/heredocs, and package scripts. Browser counts must still be
  correct (`--workers=1`, one browser per process, cleanup in `finally`).
- The script returns an explicit denial on its own parsing errors. Codex
  itself can fail open if a hook cannot start, times out, or emits malformed
  output. Keep the hook executable and inspect `/hooks` after upgrades.

Official documentation: [global AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[hook discovery, trust, and protocol](https://learn.chatgpt.com/docs/hooks).
Source checked: [exec command hook payload](https://github.com/openai/codex/blob/rust-v0.159.3/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs),
[hook runtime cwd](https://github.com/openai/codex/blob/rust-v0.159.3/codex-rs/core/src/hook_runtime.rs),
[trust and discovery](https://github.com/openai/codex/blob/rust-v0.159.3/codex-rs/hooks/src/engine/discovery.rs).

## Regression checks

```sh
python3 -m unittest discover -s ~/.codex/tests -p '*_test.py' -v
bash -n ~/.codex/bin/heavy-gate
```

Tests use temporary lock directories and fake systemd commands; they do not
launch browsers or alter the machine's shared limits. They cover detection,
Codex payload/denial compatibility, admission, isolation failures, scope exit
status, descendant ownership, and cleanup. Real cgroup verification can run a
small command through the gate; never allocate gigabytes just to test OOM.
