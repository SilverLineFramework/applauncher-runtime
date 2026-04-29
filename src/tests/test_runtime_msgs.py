import unittest

from common.exception import MissingField, NotDeclaredField
from model import *


MIO_TEMPLATE = "realm/s/{namespaced_scene}/p/{module_uuid}"
RT_UUID  = 'c950272a-905b-4cc3-8b2d-c38a779806ef'
MOD_UUID = '070aebda-390c-4529-b6ea-730eede590a8'


def make_topics(**overrides):
    defaults = dict(
        runtimes="realm/proc/runtimes",
        modules="realm/proc/modules",
        mio=MIO_TEMPLATE,
    )
    return RuntimeTopics(**{**defaults, **overrides})


def make_runtime(topics, **overrides):
    defaults = dict(
        topics=topics,
        uuid=RT_UUID,
        name='test_rt',
        runtime_type=RuntimeLauncherTypes.module_container,
        max_nmodules=10,
        apis=["python:python3"],
    )
    return Runtime(**{**defaults, **overrides})


def make_module(topics, **overrides):
    defaults = dict(
        uuid=MOD_UUID,
        name='test_mod',
        file='arena/image-switcher',
        filetype='PY',
        parent=RT_UUID,
    )
    return Module(topics.mio, **{**defaults, **overrides})


# ---------------------------------------------------------------------------
# RuntimeTopics
# ---------------------------------------------------------------------------

class TestRuntimeTopics(unittest.TestCase):

    def test_valid_construction(self):
        t = make_topics()
        self.assertEqual(t.runtimes, "realm/proc/runtimes")
        self.assertEqual(t.modules, "realm/proc/modules")
        self.assertIn('{namespaced_scene}', t.mio)

    def test_missing_mio_raises(self):
        with self.assertRaises(MissingField):
            RuntimeTopics(runtimes="realm/runtimes", modules="realm/modules")

    def test_missing_modules_raises(self):
        with self.assertRaises(MissingField):
            RuntimeTopics(runtimes="realm/runtimes", mio=MIO_TEMPLATE)

    def test_extra_keys_allowed(self):
        t = RuntimeTopics(runtimes="r", modules="m", mio=MIO_TEMPLATE, custom_key="x")
        self.assertEqual(t['custom_key'], "x")

    def test_keepalive_returns_runtimes(self):
        t = make_topics()
        self.assertEqual(t.keepalive, t.runtimes)


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------

class TestRuntime(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.topics = make_topics()
        cls.rt = make_runtime(cls.topics)
        cls.rt_full = make_runtime(
            cls.topics,
            is_orchestration_runtime=True,
            tags=["arena-py", "containerized"],
        )

    def test_required_field_missing_raises(self):
        with self.assertRaises(MissingField):
            Runtime(topics=self.topics, uuid=RT_UUID, name='rt',
                    runtime_type=RuntimeLauncherTypes.module_container,
                    max_nmodules=10)  # missing apis

    def test_undeclared_field_raises(self):
        with self.assertRaises(NotDeclaredField):
            make_runtime(self.topics, _unknown_field_='value')

    def test_apis_string_split_into_list(self):
        rt = make_runtime(self.topics, apis="python:python3 wasm:wasi_preview_1")
        self.assertEqual(rt.apis, ["python:python3", "wasm:wasi_preview_1"])

    def test_apis_list_kept_as_is(self):
        self.assertEqual(self.rt.apis, ["python:python3"])

    # --- create message ---

    def test_create_message_action(self):
        msg = self.rt.create_runtime_msg()
        self.assertEqual(msg.payload['action'], 'create')
        self.assertEqual(msg.payload['type'], 'req')

    def test_create_message_topic(self):
        msg = self.rt.create_runtime_msg()
        self.assertEqual(msg.topic, 'realm/proc/runtimes')

    def test_create_message_data_fields(self):
        msg = self.rt.create_runtime_msg()
        d = msg.payload['data']
        self.assertEqual(d['uuid'], RT_UUID)
        self.assertEqual(d['name'], 'test_rt')
        self.assertEqual(d['type'], 'runtime')
        self.assertEqual(d['runtime_type'], 'module-container')
        self.assertEqual(d['max_nmodules'], 10)
        self.assertEqual(d['apis'], ['python:python3'])

    def test_create_message_from_field(self):
        msg = self.rt.create_runtime_msg()
        self.assertEqual(msg.payload['from'], RT_UUID)

    def test_create_message_optional_fields_none_when_not_set(self):
        msg = self.rt.create_runtime_msg()
        d = msg.payload['data']
        self.assertIsNone(d['is_orchestration_runtime'])
        self.assertIsNone(d['tags'])

    def test_create_message_optional_fields_when_set(self):
        msg = self.rt_full.create_runtime_msg()
        d = msg.payload['data']
        self.assertTrue(d['is_orchestration_runtime'])
        self.assertEqual(d['tags'], ["arena-py", "containerized"])

    def test_create_message_object_id_is_unique(self):
        msg1 = self.rt.create_runtime_msg()
        msg2 = self.rt.create_runtime_msg()
        self.assertNotEqual(msg1.payload['object_id'], msg2.payload['object_id'])

    # --- delete message ---

    def test_delete_message_action(self):
        msg = self.rt.delete_runtime_msg()
        self.assertEqual(msg.payload['action'], 'delete')
        self.assertEqual(msg.payload['type'], 'req')

    def test_delete_message_same_topic_as_create(self):
        create = self.rt.create_runtime_msg()
        delete = self.rt.delete_runtime_msg()
        self.assertEqual(create.topic, delete.topic)

    def test_delete_message_data_has_uuid(self):
        msg = self.rt.delete_runtime_msg()
        self.assertEqual(msg.payload['data']['uuid'], RT_UUID)

    # --- keepalive message ---

    def test_keepalive_message_action(self):
        msg = self.rt.keepalive_msg(children=[])
        self.assertEqual(msg.payload['action'], 'update')
        self.assertEqual(msg.payload['type'], 'req')

    def test_keepalive_message_topic(self):
        msg = self.rt.keepalive_msg(children=[])
        self.assertEqual(msg.topic, 'realm/proc/runtimes')

    def test_keepalive_message_includes_children(self):
        children = [{'uuid': 'abc', 'name': 'mod1'}]
        msg = self.rt.keepalive_msg(children)
        self.assertEqual(msg.payload['data']['children'], children)

    def test_keepalive_message_empty_children(self):
        msg = self.rt.keepalive_msg([])
        self.assertEqual(msg.payload['data']['children'], [])


# ---------------------------------------------------------------------------
# Module
# ---------------------------------------------------------------------------

class TestModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.topics = make_topics()
        cls.module = make_module(cls.topics)

    def test_required_field_missing_raises(self):
        with self.assertRaises(MissingField):
            Module(MIO_TEMPLATE, uuid=MOD_UUID, name='m', file='f.py', filetype='PY')
            # missing parent

    def test_mio_topic_contains_module_uuid(self):
        self.assertIn(MOD_UUID, self.module.mio)

    def test_mio_topic_contains_default_scene(self):
        self.assertIn('public', self.module.mio)
        self.assertIn('default', self.module.mio)

    def test_stdout_topic_is_under_mio(self):
        self.assertTrue(self.module.topics['stdout'].startswith(self.module.mio))

    def test_stdin_topic_is_under_mio(self):
        self.assertTrue(self.module.topics['stdin'].startswith(self.module.mio))

    def test_stderr_topic_is_under_mio(self):
        self.assertTrue(self.module.topics['stderr'].startswith(self.module.mio))

    def test_custom_scene_appears_in_mio(self):
        mod = Module(MIO_TEMPLATE, uuid=MOD_UUID, name='m', file='f.py',
                     filetype='PY', parent=RT_UUID, scene='mynamespace/myscene')
        self.assertIn('mynamespace', mod.mio)
        self.assertIn('myscene', mod.mio)

    def test_env_dict(self):
        mod = make_module(self.topics, env={'KEY': 'val'})
        self.assertEqual(mod.env, {'KEY': 'val'})

    def test_env_list(self):
        mod = make_module(self.topics, env=['KEY=val'])
        self.assertEqual(mod.env, ['KEY=val'])

    def test_args_list(self):
        mod = make_module(self.topics, args=['--verbose', '--output', 'out.txt'])
        self.assertEqual(mod.args, ['--verbose', '--output', 'out.txt'])

    # --- confirm message ---

    def test_confirm_msg_preserves_object_id(self):
        sl = SlMsgs(RT_UUID)
        req = sl.req(self.topics.modules, 'create', self.module)
        confirm = self.module.confirm_msg(req)
        self.assertEqual(confirm.payload['object_id'], req.payload['object_id'])

    def test_confirm_msg_action_matches_request(self):
        sl = SlMsgs(RT_UUID)
        req = sl.req(self.topics.modules, 'create', self.module)
        confirm = self.module.confirm_msg(req)
        self.assertEqual(confirm.payload['action'], 'create')

    def test_confirm_msg_type_is_response(self):
        sl = SlMsgs(RT_UUID)
        req = sl.req(self.topics.modules, 'create', self.module)
        confirm = self.module.confirm_msg(req)
        self.assertEqual(confirm.payload['type'], 'resp')

    def test_confirm_msg_result_is_ok(self):
        sl = SlMsgs(RT_UUID)
        req = sl.req(self.topics.modules, 'create', self.module)
        confirm = self.module.confirm_msg(req)
        self.assertEqual(confirm.payload['data']['result'], 'ok')

    def test_confirm_msg_topic_is_mio(self):
        sl = SlMsgs(RT_UUID)
        req = sl.req(self.topics.modules, 'create', self.module)
        confirm = self.module.confirm_msg(req)
        self.assertEqual(confirm.topic, self.module.mio)

    def test_confirm_msg_from_is_parent_uuid(self):
        sl = SlMsgs(RT_UUID)
        req = sl.req(self.topics.modules, 'create', self.module)
        confirm = self.module.confirm_msg(req)
        self.assertEqual(confirm.payload['from'], RT_UUID)

    # --- delete message ---

    def test_delete_msg_action(self):
        msg = self.module.delete_msg()
        self.assertEqual(msg.payload['action'], 'delete')

    def test_delete_msg_contains_uuid(self):
        msg = self.module.delete_msg()
        self.assertEqual(msg.payload['data']['uuid'], MOD_UUID)

    # --- keepalive_attrs ---

    def test_keepalive_attrs_includes_stats(self):
        stats = ModuleStats(
            cpu_usage_percent=3.5, mem_usage=50000000,
            network_rx_mb=0.1, network_tx_mb=0.05,
            network_rx_pkts=100, network_tx_pkts=50,
        )
        ka = self.module.keepalive_attrs(stats)
        self.assertEqual(ka['uuid'], MOD_UUID)
        self.assertEqual(ka['cpu_usage_percent'], 3.5)
        self.assertEqual(ka['mem_usage'], 50000000)

    def test_keepalive_attrs_none_returns_none(self):
        self.assertIsNone(self.module.keepalive_attrs(None))

    def test_keepalive_attrs_includes_module_fields(self):
        stats = ModuleStats(
            cpu_usage_percent=0.0, mem_usage=0,
            network_rx_mb=0.0, network_tx_mb=0.0,
            network_rx_pkts=0, network_tx_pkts=0,
        )
        ka = self.module.keepalive_attrs(stats)
        self.assertEqual(ka['name'], 'test_mod')
        self.assertEqual(ka['filetype'], 'PY')


if __name__ == '__main__':
    unittest.main()
