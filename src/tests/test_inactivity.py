"""
Unit tests for inactivity detection:
  - PythonLauncher.is_active() stat-based logic
  - RuntimeMngr inactivity monitor thread behaviour
"""
import time
import threading
import unittest
from unittest.mock import MagicMock, patch

from common import LauncherException
from runtime.runtime_mngr import RuntimeMngr


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stats(cpu=0.0, rx=0, tx=0, blkio=0, mem=0):
    return {'cpu_percent': cpu, 'rx_bytes': rx, 'tx_bytes': tx,
            'blkio_bytes': blkio, 'mem_usage': mem}


_LAUNCHER_SETTINGS = {
    'cmd': '/entrypoint.sh',
    'pipe_stdout': False,
    'docker': {'image': 'test-image', 'workdir': '/usr/src/app'},
    'inactivity_cpu_threshold_percent': 0.5,
    'inactivity_net_threshold_bytes': 0,
    'inactivity_blkio_threshold_bytes': 0,
}

_RT_CFG = {
    "runtime": {
        "uuid": "deadbeef-dead-beef-dead-beefdeadbeef",
        "name": "unit-test-rt",
        "runtime_type": "containerized-modules",
        "max_nmodules": 10,
        "apis": "python:python3",
        "realm": "realm",
        "namespace": "public",
        "reg_attempts": -1,
        "reg_timeout_seconds": 5,
        "reg_fail_error": False,
        "ka_interval_sec": None,
        "is_orchestration_runtime": False,
        "tags": [],
    },
    "topics": {
        "runtimes": "realm/runtimes",
        "modules": "realm/modules",
        "mio": "realm/s/{namespaced_scene}/p/{module_uuid}",
    }
}


def _make_launcher(settings_overrides=None):
    """Return a PythonLauncher with all external I/O mocked."""
    from launcher.python_launcher import PythonLauncher
    from model import Module, RuntimeTopics

    settings = {**_LAUNCHER_SETTINGS, **(settings_overrides or {})}

    with patch('launcher.docker_client.docker'), \
         patch('common.utils.ClassUtils.class_instance_from_settings_class_path'):
        topics = RuntimeTopics(
            runtimes='realm/runtimes',
            modules='realm/modules',
            mio='realm/{namespaced_scene}/{module_uuid}',
        )
        module = Module(
            topics.mio,
            uuid='aaa-bbb-ccc',
            name='test-mod',
            file='test.py',
            filetype='PY',
            parent='parent-uuid',
        )
        launcher = PythonLauncher(launcher_settings=settings, module=module)

    return launcher


# ---------------------------------------------------------------------------
# PythonLauncher.is_active()
# ---------------------------------------------------------------------------

class TestIsActive(unittest.TestCase):

    def setUp(self):
        self.launcher = _make_launcher()

    # --- baseline (first call) ---

    def test_first_call_always_active_even_with_zero_stats(self):
        self.launcher._docker_client.get_stats = MagicMock(return_value=_stats())
        self.assertTrue(self.launcher.is_active())

    def test_first_call_sets_prev_counters(self):
        self.launcher._docker_client.get_stats = MagicMock(
            return_value=_stats(rx=500, tx=100, blkio=200))
        self.launcher.is_active()
        self.assertEqual(self.launcher._prev_net_bytes, 600)
        self.assertEqual(self.launcher._prev_blkio_bytes, 200)

    # --- idle detection ---

    def test_idle_when_all_zeros_after_baseline(self):
        self.launcher._docker_client.get_stats = MagicMock(return_value=_stats())
        self.launcher.is_active()         # baseline
        self.assertFalse(self.launcher.is_active())

    def test_idle_when_cpu_equals_threshold(self):
        """Exactly at threshold is NOT considered active (strictly greater required)."""
        self.launcher._docker_client.get_stats = MagicMock(
            return_value=_stats(cpu=0.5))  # threshold is 0.5
        self.launcher.is_active()
        self.assertFalse(self.launcher.is_active())

    def test_idle_sustained_over_multiple_polls(self):
        self.launcher._docker_client.get_stats = MagicMock(return_value=_stats())
        self.launcher.is_active()         # baseline
        for _ in range(5):
            self.assertFalse(self.launcher.is_active())

    # --- CPU activity ---

    def test_active_when_cpu_above_threshold(self):
        self.launcher._docker_client.get_stats = MagicMock(return_value=_stats(cpu=1.0))
        self.launcher.is_active()
        self.assertTrue(self.launcher.is_active())

    def test_custom_cpu_threshold_respected(self):
        launcher = _make_launcher({'inactivity_cpu_threshold_percent': 5.0})
        launcher._docker_client.get_stats = MagicMock(return_value=_stats(cpu=3.0))
        launcher.is_active()
        self.assertFalse(launcher.is_active())  # 3.0 < 5.0 → idle

    def test_active_cpu_above_custom_threshold(self):
        launcher = _make_launcher({'inactivity_cpu_threshold_percent': 5.0})
        launcher._docker_client.get_stats = MagicMock(return_value=_stats(cpu=6.0))
        launcher.is_active()
        self.assertTrue(launcher.is_active())   # 6.0 > 5.0 → active

    # --- network activity ---

    def test_active_when_rx_bytes_increased(self):
        self.launcher._docker_client.get_stats = MagicMock(side_effect=[
            _stats(rx=1000),
            _stats(rx=2000),
        ])
        self.launcher.is_active()
        self.assertTrue(self.launcher.is_active())

    def test_active_when_tx_bytes_increased(self):
        self.launcher._docker_client.get_stats = MagicMock(side_effect=[
            _stats(tx=0),
            _stats(tx=500),
        ])
        self.launcher.is_active()
        self.assertTrue(self.launcher.is_active())

    def test_active_when_rx_plus_tx_sum_exceeds_threshold(self):
        """rx and tx are summed before comparing against threshold."""
        launcher = _make_launcher({'inactivity_net_threshold_bytes': 500})
        launcher._docker_client.get_stats = MagicMock(side_effect=[
            _stats(rx=0, tx=0),
            _stats(rx=300, tx=300),   # sum = 600 > 500
        ])
        launcher.is_active()
        self.assertTrue(launcher.is_active())

    def test_idle_when_net_delta_at_threshold(self):
        """Net delta exactly equal to threshold is NOT active."""
        launcher = _make_launcher({'inactivity_net_threshold_bytes': 500})
        launcher._docker_client.get_stats = MagicMock(side_effect=[
            _stats(rx=0),
            _stats(rx=500),  # delta == threshold → idle
        ])
        launcher.is_active()
        self.assertFalse(launcher.is_active())

    def test_active_when_net_delta_exceeds_threshold(self):
        launcher = _make_launcher({'inactivity_net_threshold_bytes': 500})
        launcher._docker_client.get_stats = MagicMock(side_effect=[
            _stats(rx=0),
            _stats(rx=501),
        ])
        launcher.is_active()
        self.assertTrue(launcher.is_active())

    # --- disk I/O activity ---

    def test_active_when_blkio_bytes_increased(self):
        self.launcher._docker_client.get_stats = MagicMock(side_effect=[
            _stats(blkio=0),
            _stats(blkio=4096),
        ])
        self.launcher.is_active()
        self.assertTrue(self.launcher.is_active())

    def test_custom_blkio_threshold_respected(self):
        launcher = _make_launcher({'inactivity_blkio_threshold_bytes': 8192})
        launcher._docker_client.get_stats = MagicMock(side_effect=[
            _stats(blkio=0),
            _stats(blkio=4096),  # below threshold
        ])
        launcher.is_active()
        self.assertFalse(launcher.is_active())

    # --- error handling ---

    def test_stats_exception_treated_as_active(self):
        """LauncherException from get_stats → assume active (safe default)."""
        self.launcher._docker_client.get_stats = MagicMock(
            side_effect=LauncherException("container not running"))
        self.assertTrue(self.launcher.is_active())

    def test_stats_exception_after_baseline_treated_as_active(self):
        self.launcher._docker_client.get_stats = MagicMock(side_effect=[
            _stats(),
            LauncherException("gone"),
        ])
        self.launcher.is_active()
        self.assertTrue(self.launcher.is_active())

    # --- baseline advances ---

    def test_baseline_advances_so_traffic_burst_then_silence_is_inactive(self):
        self.launcher._docker_client.get_stats = MagicMock(side_effect=[
            _stats(rx=0),      # call 1: set baseline
            _stats(rx=1000),   # call 2: +1000 → active
            _stats(rx=1000),   # call 3: no change → inactive
        ])
        self.launcher.is_active()              # baseline
        self.assertTrue(self.launcher.is_active())   # burst
        self.assertFalse(self.launcher.is_active())  # silence

    def test_prev_counters_update_after_each_call(self):
        self.launcher._docker_client.get_stats = MagicMock(side_effect=[
            _stats(rx=100),
            _stats(rx=200),
        ])
        self.launcher.is_active()
        self.assertEqual(self.launcher._prev_net_bytes, 100)
        self.launcher.is_active()
        self.assertEqual(self.launcher._prev_net_bytes, 200)


# ---------------------------------------------------------------------------
# RuntimeMngr inactivity monitor
# ---------------------------------------------------------------------------

class TestInactivityMonitor(unittest.TestCase):
    """
    Tests for RuntimeMngr's inactivity monitor.
    The RuntimeMngr is constructed without pubsub connectivity; the monitor
    thread is started manually, and modules are injected directly into the
    private __modules dict so no Docker or MQTT is required.
    """

    def setUp(self):
        self.rtmngr = RuntimeMngr(**_RT_CFG)
        # Provide a mock pubsub client so __module_exit can publish
        self.rtmngr._RuntimeMngr__pubsub_client = MagicMock()

    def tearDown(self):
        # Signal any running monitor/keepalive threads to exit
        self.rtmngr._RuntimeMngr__ka_exit.set()
        self.rtmngr._RuntimeMngr__exited = True

    def _add_module(self, mod_uuid, *, idle_secs=0, is_active=True,
                    stop_raises=False):
        """Inject a mock MngrModule into the runtime manager."""
        launcher = MagicMock()
        launcher.is_active.return_value = is_active
        launcher.get_stats.return_value = None

        mod = MagicMock()
        mod.module_launcher = launcher
        mod.module.uuid = mod_uuid
        mod.module.delete_msg.return_value = MagicMock()
        mod.last_active_at = time.time() - idle_secs

        if stop_raises:
            mod.stop.side_effect = LauncherException("not running")
        else:
            mod.stop.return_value = None

        self.rtmngr._RuntimeMngr__modules[mod_uuid] = mod
        return mod

    def _run_monitor_cycle(self, check_interval=0.05, timeout_sec=30,
                           run_for=0.2):
        """Run the inactivity monitor in a daemon thread for `run_for` seconds."""
        t = threading.Thread(
            target=self.rtmngr._RuntimeMngr__inactivity_monitor,
            args=(check_interval, timeout_sec),
            daemon=True,
        )
        t.start()
        time.sleep(run_for)
        self.rtmngr._RuntimeMngr__ka_exit.set()
        t.join(timeout=3)

    # --- module_exists (thread-safe lookup) ---

    def test_module_exists_true(self):
        self._add_module('mod-exists')
        self.assertTrue(self.rtmngr.module_exists('mod-exists'))

    def test_module_exists_false(self):
        self.assertFalse(self.rtmngr.module_exists('no-such-module'))

    def test_module_exists_false_after_removal(self):
        self._add_module('mod-tmp')
        del self.rtmngr._RuntimeMngr__modules['mod-tmp']
        self.assertFalse(self.rtmngr.module_exists('mod-tmp'))

    # --- __delete_inactive_module ---

    def test_delete_inactive_calls_stop(self):
        mod = self._add_module('mod-a')
        self.rtmngr._RuntimeMngr__delete_inactive_module('mod-a')
        mod.stop.assert_called_once()

    def test_delete_inactive_unknown_uuid_is_noop(self):
        self.rtmngr._RuntimeMngr__delete_inactive_module('ghost-uuid')
        # no exception raised

    def test_delete_inactive_stop_raises_removes_module(self):
        """When stop() raises, __module_exit must remove the module."""
        self._add_module('mod-b', stop_raises=True)
        self.rtmngr._RuntimeMngr__delete_inactive_module('mod-b')
        self.assertNotIn('mod-b', self.rtmngr._RuntimeMngr__modules)

    def test_delete_inactive_stop_raises_publishes_delete_msg(self):
        self._add_module('mod-c', stop_raises=True)
        self.rtmngr._RuntimeMngr__delete_inactive_module('mod-c')
        self.rtmngr._RuntimeMngr__pubsub_client.message_publish.assert_called_once()

    # --- monitor thread: deletion ---

    def test_monitor_deletes_module_idle_beyond_timeout(self):
        self._add_module('mod-long-idle', idle_secs=120, is_active=False,
                         stop_raises=True)
        self._run_monitor_cycle(timeout_sec=30)
        self.assertNotIn('mod-long-idle', self.rtmngr._RuntimeMngr__modules)

    def test_monitor_keeps_module_idle_within_timeout(self):
        self._add_module('mod-recent-idle', idle_secs=5, is_active=False)
        self._run_monitor_cycle(timeout_sec=30)
        self.assertIn('mod-recent-idle', self.rtmngr._RuntimeMngr__modules)

    def test_monitor_keeps_active_module_regardless_of_idle_time(self):
        self._add_module('mod-active', idle_secs=120, is_active=True)
        self._run_monitor_cycle(timeout_sec=30)
        self.assertIn('mod-active', self.rtmngr._RuntimeMngr__modules)

    # --- monitor thread: timestamp updates ---

    def test_monitor_updates_last_active_at_for_active_module(self):
        mod = self._add_module('mod-ts', idle_secs=60, is_active=True)
        old_ts = mod.last_active_at
        self._run_monitor_cycle(timeout_sec=30)
        self.assertGreater(mod.last_active_at, old_ts)

    def test_monitor_does_not_update_last_active_at_for_idle_module(self):
        mod = self._add_module('mod-idle-ts', idle_secs=5, is_active=False)
        expected_ts = mod.last_active_at
        self._run_monitor_cycle(timeout_sec=30)
        self.assertAlmostEqual(mod.last_active_at, expected_ts, delta=0.5)

    # --- monitor thread: mixed modules ---

    def test_monitor_deletes_only_idle_modules_among_mixed(self):
        self._add_module('idle-mod', idle_secs=120, is_active=False,
                         stop_raises=True)
        self._add_module('active-mod', idle_secs=0, is_active=True)
        self._run_monitor_cycle(timeout_sec=30)
        self.assertNotIn('idle-mod', self.rtmngr._RuntimeMngr__modules)
        self.assertIn('active-mod', self.rtmngr._RuntimeMngr__modules)

    def test_monitor_handles_is_active_exception_without_crashing(self):
        """Exceptions from is_active() must not kill the monitor thread."""
        mod = self._add_module('mod-exc')
        mod.module_launcher.is_active.side_effect = Exception("unexpected!")
        # monitor must survive the cycle
        self._run_monitor_cycle(timeout_sec=30)

    # --- monitor thread: exits cleanly ---

    def test_monitor_exits_when_ka_exit_set(self):
        t = threading.Thread(
            target=self.rtmngr._RuntimeMngr__inactivity_monitor,
            args=(0.05, 30),
            daemon=True,
        )
        t.start()
        self.rtmngr._RuntimeMngr__ka_exit.set()
        t.join(timeout=2)
        self.assertFalse(t.is_alive())


if __name__ == '__main__':
    unittest.main()
