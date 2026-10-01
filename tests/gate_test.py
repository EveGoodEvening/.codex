"""Exercise admission/cleanup without starting browsers or consuming shared slots."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

GATE = Path(__file__).resolve().parents[1] / 'bin' / 'heavy-gate'


class GateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        mock_bin = self.root / 'bin'
        mock_bin.mkdir()
        self.locks = self.root / 'locks'
        self.locks.mkdir()
        self.marker = self.root / 'launched'
        self.active = self.root / 'descendants-active'
        self.log = self.root / 'systemd-log'
        self.env = {
            **os.environ,
            'PATH': str(mock_bin) + os.pathsep + os.environ['PATH'],
            'HEAVY_GATE_DIR': str(self.locks),
            'HEAVY_GATE_SLOTS': '2',
            'HEAVY_GATE_MIN_FREE_MB': '0',
            'HEAVY_GATE_SETTLE': '0',
            'HEAVY_GATE_MEM_MAX': '6G',
            'GATE_TEST_ROOT': str(self.root),
            'GATE_TEST_NO_SYSTEMD': '0',
            'GATE_TEST_SCOPE_FAILURE': '0',
        }
        mock = '''
import json, os, pathlib, subprocess, sys
root = pathlib.Path(os.environ['GATE_TEST_ROOT'])
args = sys.argv[1:]
if pathlib.Path(sys.argv[0]).name == 'systemctl':
    if 'show-environment' in args:
        sys.exit(int(os.environ['GATE_TEST_NO_SYSTEMD']))
    if 'show' in args:
        print('active' if (root / 'descendants-active').exists() else 'inactive')
    if 'stop' in args:
        (root / 'stopped-unit').write_text(args[-1])
        (root / 'descendants-active').unlink(missing_ok=True)
else:
    (root / 'systemd-log').write_text(json.dumps(args))
    if os.environ['GATE_TEST_SCOPE_FAILURE'] == '1':
        sys.exit(73)
    sys.exit(subprocess.run(args[args.index('--') + 1:]).returncode)
'''
        for name in ('systemctl', 'systemd-run'):
            script = mock_bin / name
            script.write_text('#!' + sys.executable + '\n' + mock)
            script.chmod(0o755)

    def command(self, *gate_args, exit_code=0):
        return [str(GATE), *gate_args, '--', sys.executable, '-c',
                'from pathlib import Path; import sys; '
                'Path(sys.argv[1]).write_text("started"); sys.exit(int(sys.argv[2]))',
                str(self.marker), str(exit_code)]

    def run_gate(self, *gate_args, exit_code=0):
        return subprocess.run(self.command(*gate_args, exit_code=exit_code), env=self.env,
                              text=True, capture_output=True, timeout=10)

    def start_gate(self, *gate_args):
        process = subprocess.Popen(self.command(*gate_args), env=self.env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        def cleanup():
            if process.poll() is None:
                process.terminate()
            process.communicate(timeout=10)
        self.addCleanup(cleanup)
        return process

    def wait_until(self, predicate):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.025)
        self.fail('condition did not become true before deadline')

    def slot_is_free(self, number):
        with (self.locks / f'slot-{number}').open('a+') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except BlockingIOError:
                return False

    def test_isolation_unavailable_never_executes_command(self):
        self.env['GATE_TEST_NO_SYSTEMD'] = '1'
        result = self.run_gate()
        self.assertEqual(result.returncode, 69)
        self.assertIn('refusing uncapped execution', result.stderr)
        self.assertFalse(self.marker.exists())

    def test_scope_creation_failure_never_falls_back(self):
        self.env['GATE_TEST_SCOPE_FAILURE'] = '1'
        self.assertEqual(self.run_gate().returncode, 73)
        self.assertFalse(self.marker.exists())
        self.assertTrue(self.slot_is_free(0))

    def test_scoped_command_preserves_exit_status_and_memory_limits(self):
        result = self.run_gate('-n', '2', '-m', '256M', exit_code=7)
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertTrue(self.marker.exists())
        args = json.loads(self.log.read_text())
        self.assertIn('--scope', args)
        self.assertIn('MemoryMax=256M', args)
        self.assertIn('MemorySwapMax=0', args)
        self.assertTrue(self.slot_is_free(0))
        self.assertTrue(self.slot_is_free(1))

    def test_invalid_limits_rejected_before_launch(self):
        for args in (('-n', '0'), ('-n', '3'), ('-m', 'infinity'), ('-m', '0'), ('-m', '-1G')):
            with self.subTest(args=args):
                self.assertEqual(self.run_gate(*args).returncode, 64)
        self.env['HEAVY_GATE_SLOTS'] = '3'
        self.assertEqual(self.run_gate().returncode, 64)
        self.assertFalse(self.marker.exists())

    def test_other_clients_locks_block_admission(self):
        with (self.locks / 'slot-0').open('a+') as first, (self.locks / 'slot-1').open('a+') as second:
            fcntl.flock(first, fcntl.LOCK_EX)
            fcntl.flock(second, fcntl.LOCK_EX)
            process = self.start_gate()
            time.sleep(0.3)
            self.assertIsNone(process.poll())
            self.assertFalse(self.marker.exists())
            fcntl.flock(first, fcntl.LOCK_UN)
            self.wait_until(self.marker.exists)
        self.assertEqual(process.wait(timeout=5), 0)

    def test_two_slot_request_does_not_hold_one_slot_while_waiting(self):
        with (self.locks / 'slot-1').open('a+') as other_client:
            fcntl.flock(other_client, fcntl.LOCK_EX)
            process = self.start_gate('-n', '2')
            self.wait_until(lambda: (self.locks / 'slot-0').exists())
            time.sleep(0.1)
            self.assertTrue(self.slot_is_free(0))
            self.assertFalse(self.marker.exists())
            process.terminate()
            self.assertEqual(process.wait(timeout=5), 143)

    def test_low_memory_waits_without_starting_work(self):
        self.env['HEAVY_GATE_MIN_FREE_MB'] = '999999999'
        process = self.start_gate()
        self.wait_until(lambda: (self.locks / 'launch').exists())
        time.sleep(0.1)
        self.assertFalse(self.marker.exists())
        self.assertTrue(self.slot_is_free(0))
        process.terminate()
        self.assertEqual(process.wait(timeout=5), 143)

    def test_slots_remain_held_until_descendants_exit(self):
        self.active.touch()
        process = self.start_gate()
        self.wait_until(self.marker.exists)
        self.assertIsNone(process.poll())
        self.assertFalse(self.slot_is_free(0))
        self.active.unlink()
        self.assertEqual(process.wait(timeout=5), 0)
        self.assertTrue(self.slot_is_free(0))

    def test_termination_stops_only_the_owned_scope(self):
        self.active.touch()
        process = self.start_gate()
        self.wait_until(self.marker.exists)
        args = json.loads(self.log.read_text())
        unit = next(arg.split('=', 1)[1] for arg in args if arg.startswith('--unit='))
        process.terminate()
        self.assertEqual(process.wait(timeout=5), 143)
        self.assertEqual((self.root / 'stopped-unit').read_text(), unit)
        self.assertTrue(self.slot_is_free(0))


if __name__ == '__main__':
    unittest.main()
