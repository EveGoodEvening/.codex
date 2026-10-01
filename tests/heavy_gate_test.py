import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / 'bin' / 'heavy-gate-hook'
GATE = str(Path.home() / '.codex' / 'bin' / 'heavy-gate')
CLAUDE_GATE = str(Path.home() / '.claude' / 'bin' / 'heavy-gate')
OMP_GATE = str(Path.home() / '.omp' / 'bin' / 'heavy-gate')


class LaunchPolicyTest(unittest.TestCase):
    def invoke(self, payload):
        result = subprocess.run([str(HOOK)], input=payload, text=True, capture_output=True, check=True)
        if not result.stdout.strip():
            return None
        response = json.loads(result.stdout)['hookSpecificOutput']
        self.assertEqual(response['hookEventName'], 'PreToolUse')
        self.assertEqual(response['permissionDecision'], 'deny')
        self.assertIsInstance(response['permissionDecisionReason'], str)
        return response

    def blocked(self, command, cwd=None):
        return self.invoke(json.dumps({
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': command},
            'cwd': str(cwd or ROOT),
        })) is not None

    def test_gate_only_covers_its_own_simple_command(self):
        self.assertFalse(self.blocked(f'{GATE} -- npx playwright test'))
        self.assertTrue(self.blocked(f'{GATE} -- true && npx playwright test'))
        self.assertTrue(self.blocked('echo heavy-gate && npx playwright test'))

    def test_only_installed_codex_claude_and_omp_gates_are_trusted(self):
        for gate in (GATE, CLAUDE_GATE, OMP_GATE, '~/.codex/bin/heavy-gate'):
            with self.subTest(gate=gate):
                self.assertFalse(self.blocked(f'{gate} -- npx playwright test'))
        with tempfile.TemporaryDirectory() as tmp:
            counterfeit = Path(tmp) / 'heavy-gate'
            counterfeit.write_text('#!/bin/sh\nexec "$@"\n')
            self.assertTrue(self.blocked(f'{counterfeit} -- npx playwright test'))

    def test_timeout_cannot_wrap_a_queued_gate(self):
        for command in (
            f'timeout 30 {GATE} -- node smoke.js',
            f'timeout -k 5 30 bash -c "{GATE} -- node smoke.js"',
        ):
            with self.subTest(command=command):
                self.assertTrue(self.blocked(command))
        self.assertFalse(self.blocked(f'{GATE} --status'))
        self.assertFalse(self.blocked('timeout 30 printf ordinary-command'))

    def test_inline_runtimes_and_heredocs(self):
        for command in (
            '''bun -e 'require("puppeteer").launch()' ''',
            '''bun --smol -e 'require("puppeteer").launch()' ''',
            '''bun --cwd /tmp -e 'require("puppeteer").launch()' ''',
            '''node -e 'require("playwright").chromium.launch()' ''',
            '''deno eval 'import("playwright")' ''',
            'python3 -c "from playwright.sync_api import sync_playwright"',
            "python3 - <<'PY'\nfrom playwright.sync_api import sync_playwright\nPY",
        ):
            with self.subTest(command=command):
                self.assertTrue(self.blocked(command))
        self.assertFalse(self.blocked('bun -e "console.log(2+2)"'))

    def test_scripts_local_imports_and_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'runner.mjs').write_text('import "./browser.mjs";')
            (root / 'browser.mjs').write_text('import { chromium } from "playwright";')
            (root / 'smoke.sh').write_text('#!/bin/sh\nnode runner.mjs\n')
            for command in ('node runner.mjs', 'bash smoke.sh', './smoke.sh'):
                with self.subTest(command=command):
                    self.assertTrue(self.blocked(command, root))
            self.assertTrue(self.blocked(f'cd {shlex.quote(tmp)} && bash smoke.sh', ROOT))
            self.assertFalse(self.blocked(f'{GATE} -- bash smoke.sh', root))

    def test_node_preload_is_checked_before_main_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'preload.cjs').write_text('require("puppeteer").launch();')
            (root / 'unit.cjs').write_text('console.log("ordinary");')
            self.assertTrue(self.blocked('node --require ./preload.cjs unit.cjs', root))
            self.assertFalse(self.blocked('node unit.cjs', root))

    def test_npm_pre_and_post_scripts_cannot_hide_browser_launches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / 'package.json'
            for lifecycle in ('pretest', 'posttest'):
                package.write_text(json.dumps({'scripts': {'test': 'printf unit', lifecycle: 'playwright test'}}))
                with self.subTest(lifecycle=lifecycle):
                    self.assertTrue(self.blocked('npm test', root))
            package.write_text(json.dumps({'scripts': {'test': 'printf unit'}}))
            self.assertFalse(self.blocked('npm test', root))

    def test_package_runner_paths_use_selected_package_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = root / 'project'
            child.mkdir()
            (child / 'package.json').write_text(json.dumps({'scripts': {'smoke': 'node browser.mjs'}}))
            (child / 'browser.mjs').write_text('import puppeteer from "puppeteer";')
            for command in (
                'npm --prefix project run smoke', 'pnpm --dir project smoke',
                'yarn --cwd project smoke', 'bun --cwd project run smoke',
                'npm --prefix project exec -- node browser.mjs',
            ):
                with self.subTest(command=command):
                    self.assertTrue(self.blocked(command, root))

    def test_nonlaunching_cli_operations_remain_usable(self):
        for command in (
            'npx playwright --version', 'npx playwright install', 'npx playwright test --list',
            'python3 -m playwright test --list', 'chrome --version', 'firefox --help',
        ):
            with self.subTest(command=command):
                self.assertFalse(self.blocked(command))
        for command in ('chrome', 'firefox', 'electron app.js', 'npx playwright screenshot https://example.com out.png'):
            with self.subTest(command=command):
                self.assertTrue(self.blocked(command))

    def test_wrapper_option_arguments_do_not_hide_launches(self):
        for command in ('nice -n 5 npx playwright test', 'env -u DISPLAY npx playwright test', 'xvfb-run -a npx playwright test'):
            with self.subTest(command=command):
                self.assertTrue(self.blocked(command))

    def test_invalid_input_and_package_json_fail_closed(self):
        self.assertIsNotNone(self.invoke('{broken'))
        self.assertTrue(self.blocked('npx playwright test "unterminated'))
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'package.json').write_text('{broken')
            self.assertTrue(self.blocked('npm test', tmp))

    def test_recursive_package_script_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'package.json').write_text(json.dumps({'scripts': {'smoke': 'npm run smoke'}}))
            self.assertTrue(self.blocked('npm run smoke', tmp))

    def test_codex_normalized_exec_command_payload_and_recovery_message(self):
        response = self.invoke(json.dumps({
            'session_id': 'codex-session',
            'turn_id': 'codex-turn',
            'model': 'test-model',
            'permission_mode': 'bypassPermissions',
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_use_id': 'exec-command-call',
            'tool_input': {'command': 'npx playwright test --workers=1'},
            'cwd': str(ROOT),
        }))
        reason = response['permissionDecisionReason']
        self.assertIn('~/.codex/bin/heavy-gate', reason)
        self.assertIn('exec_command', reason)
        self.assertIn('write_stdin', reason)
        self.assertNotIn('run_in_background', reason)
        # Codex fails open for unsupported control fields; never emit them.
        self.assertEqual(set(response), {
            'hookEventName', 'permissionDecision', 'permissionDecisionReason',
        })

    def test_missing_or_changed_hook_protocol_fails_closed(self):
        for payload in (
            {}, [],
            {'hook_event_name': 'PreToolUse', 'tool_name': 'Bash', 'tool_input': {}},
            {'hook_event_name': 'PreToolUse', 'tool_name': 'Bash',
             'tool_input': {'command': ['npx', 'playwright', 'test']}},
            {'hook_event_name': 'PreToolUse', 'tool_name': 'exec_command',
             'tool_input': {'cmd': 'npx playwright test'}},
        ):
            with self.subTest(payload=payload):
                self.assertIsNotNone(self.invoke(json.dumps(payload)))


if __name__ == '__main__':
    unittest.main()
