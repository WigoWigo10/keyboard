"""
Tests for the Windows backend, driven with synthetic hook events.

The main suite in test_keyboard.py replaces `directkeys._os_keyboard` with a
fake, so none of it reaches `_winkeyboard`. Everything specific to this fork --
the AltGr abstraction, the event flags, the stuck key helpers -- lives there and
was consequently untested; every regression fixed in 1.1.0 would have been
caught here.

`process_key` is called directly rather than through a real hook, so these tests
need no keyboard and no message pump. They do need the Win32 API, so the whole
module is skipped off Windows.
"""

import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="the Windows backend requires the Win32 API"
)

if sys.platform == "win32":
    import directkeys
    from directkeys import _winkeyboard
    from directkeys._keyboard_event import KEY_DOWN, KEY_UP


# Scan code Windows uses for the synthetic Ctrl it injects alongside AltGr.
SYNTHETIC_CTRL_SCAN_CODE = 541
VK_RIGHT_ALT = 165
VK_LEFT_CTRL = 162
RIGHT_ALT_SCAN_CODE = 56


@pytest.fixture(autouse=True)
def clean_backend_state():
    """Every test starts from a known backend state and leaves one behind."""
    _winkeyboard._setup_name_tables()
    _winkeyboard._reset_internal_state()
    directkeys.set_alt_gr_abstraction(True)
    yield
    _winkeyboard._reset_internal_state()
    directkeys.set_alt_gr_abstraction(True)


class Collector:
    """Callback that records the events it is handed and always passes them on."""

    def __init__(self):
        self.events = []

    def __call__(self, event):
        self.events.append(event)
        return True

    @property
    def names(self):
        return [e.name for e in self.events]

    @property
    def pairs(self):
        return [(e.event_type, e.name) for e in self.events]


def feed(collector, event_type, vk, scan_code, is_extended=0, flags=0):
    return _winkeyboard.process_key(collector, event_type, vk, scan_code, is_extended, flags)


# --------------------------------------------------------------------------
# Backend wiring
# --------------------------------------------------------------------------


def test_helpers_resolve_to_the_backend_not_the_stubs():
    """Regression: these used to always fall back to the no-op stubs."""
    assert directkeys.force_reset_keyboard.__module__ == "directkeys._winkeyboard"
    assert directkeys.get_stuck_keys.__module__ == "directkeys._winkeyboard"
    assert directkeys.reset_internal_state.__module__ == "directkeys._winkeyboard"


def test_rebuild_name_tables_is_reachable_from_the_module():
    """Regression: it was nested in prepare_intercept, so the hasattr guard failed."""
    assert hasattr(_winkeyboard, "rebuild_name_tables")
    _winkeyboard.rebuild_name_tables()
    assert _winkeyboard.to_name, "the tables should be repopulated, not left empty"


def test_get_stuck_keys_returns_known_modifier_names():
    stuck = directkeys.get_stuck_keys()
    assert isinstance(stuck, list)
    assert set(stuck) <= set(_winkeyboard._modifier_vk_names.values())


# --------------------------------------------------------------------------
# Modifiers
# --------------------------------------------------------------------------


def test_get_modifiers_is_bounded_when_shift_is_held(monkeypatch):
    """Regression: GetKeyState reports 0x8000, which built a 32772-item tuple."""
    monkeypatch.setattr(_winkeyboard.user32, "GetKeyState", lambda vk: 0x8000 if vk == 0x10 else 1)
    modifiers = _winkeyboard.get_modifiers(altgr_is_pressed=True)
    assert modifiers == ("shift", "alt gr", "num lock", "caps lock", "scroll lock")


def test_get_modifiers_omits_what_is_not_pressed(monkeypatch):
    monkeypatch.setattr(_winkeyboard.user32, "GetKeyState", lambda vk: 0)
    assert _winkeyboard.get_modifiers(altgr_is_pressed=False) == ()


# --------------------------------------------------------------------------
# Event fields
# --------------------------------------------------------------------------


def test_keypad_keys_are_reported_from_the_lookup_table():
    """Regression: is_keypad was set from is_extended, close to its inverse."""
    collector = Collector()
    # Numpad 8: in the keypad table, and not an extended key.
    feed(collector, KEY_DOWN, vk=104, scan_code=72, is_extended=0)
    assert collector.events[0].is_keypad is True


def test_extended_keys_are_not_mistaken_for_keypad_keys():
    collector = Collector()
    # Up arrow: shares scan code 72 with numpad 8 but is extended, not keypad.
    feed(collector, KEY_DOWN, vk=38, scan_code=72, is_extended=1)
    assert collector.events[0].is_keypad is False


def test_scan_code_falls_back_to_the_negated_vk():
    """Regression: the `scan_code or -vk` fallback was dropped."""
    collector = Collector()
    feed(collector, KEY_DOWN, vk=65, scan_code=0)
    assert collector.events[0].scan_code == -65


def test_scan_code_is_kept_when_present():
    collector = Collector()
    feed(collector, KEY_DOWN, vk=65, scan_code=30)
    assert collector.events[0].scan_code == 30


def test_flags_reach_the_event_and_its_json():
    collector = Collector()
    feed(collector, KEY_DOWN, vk=65, scan_code=30, flags=1)
    event = collector.events[0]
    assert event.flags == 1
    assert '"flags": 1' in event.to_json()


def test_callback_return_value_is_propagated():
    """A callback that blocks an event must be able to say so."""
    assert feed(lambda event: False, KEY_DOWN, vk=65, scan_code=30) is False
    assert feed(lambda event: True, KEY_DOWN, vk=65, scan_code=30) is True


# --------------------------------------------------------------------------
# AltGr abstraction enabled (the default)
# --------------------------------------------------------------------------


def test_altgr_pair_is_merged_into_a_single_event():
    collector = Collector()
    # Windows sends Right Alt, immediately followed by a synthetic Left Ctrl.
    assert feed(collector, KEY_DOWN, VK_RIGHT_ALT, RIGHT_ALT_SCAN_CODE) is True
    assert collector.events == [], "the right alt is held back, awaiting the ctrl"

    assert feed(collector, KEY_DOWN, VK_LEFT_CTRL, SYNTHETIC_CTRL_SCAN_CODE) is True
    assert collector.pairs == [("down", "alt gr")]
    assert collector.events[0].scan_code == RIGHT_ALT_SCAN_CODE


def test_altgr_release_emits_a_single_up_event():
    collector = Collector()
    feed(collector, KEY_DOWN, VK_RIGHT_ALT, RIGHT_ALT_SCAN_CODE)
    feed(collector, KEY_DOWN, VK_LEFT_CTRL, SYNTHETIC_CTRL_SCAN_CODE)
    collector.events.clear()

    feed(collector, KEY_UP, VK_RIGHT_ALT, RIGHT_ALT_SCAN_CODE)
    assert collector.pairs == [("up", "alt gr")]


def test_synthetic_ctrl_release_is_swallowed():
    collector = Collector()
    assert feed(collector, KEY_UP, VK_LEFT_CTRL, SYNTHETIC_CTRL_SCAN_CODE) is True
    assert collector.events == []


def test_lone_right_alt_is_flushed_when_another_key_follows():
    """A real Right Alt press, with no synthetic Ctrl behind it, must not vanish."""
    collector = Collector()
    feed(collector, KEY_DOWN, VK_RIGHT_ALT, RIGHT_ALT_SCAN_CODE)
    feed(collector, KEY_DOWN, vk=65, scan_code=30)  # the letter 'a'

    assert collector.names[0] == "right alt"
    assert len(collector.events) == 2, "both the flushed alt and the new key"


def test_ordinary_keys_are_untouched_by_the_abstraction():
    collector = Collector()
    feed(collector, KEY_DOWN, vk=65, scan_code=30)
    assert collector.pairs == [("down", "a")]


# --------------------------------------------------------------------------
# AltGr abstraction disabled
# --------------------------------------------------------------------------


def test_synthetic_ctrl_is_suppressed_when_abstraction_is_off():
    directkeys.set_alt_gr_abstraction(False)
    collector = Collector()
    assert feed(collector, KEY_DOWN, VK_LEFT_CTRL, SYNTHETIC_CTRL_SCAN_CODE) is True
    assert collector.events == []


def test_right_alt_is_reported_immediately_when_abstraction_is_off():
    directkeys.set_alt_gr_abstraction(False)
    collector = Collector()
    feed(collector, KEY_DOWN, VK_RIGHT_ALT, RIGHT_ALT_SCAN_CODE)
    assert collector.pairs == [("down", "alt gr")]


def test_abstraction_state_round_trips():
    assert directkeys.get_alt_gr_abstraction_state() is True
    directkeys.set_alt_gr_abstraction(False)
    assert directkeys.get_alt_gr_abstraction_state() is False
    directkeys.set_alt_gr_abstraction(True)
    assert directkeys.get_alt_gr_abstraction_state() is True


def test_reset_internal_state_clears_a_pending_right_alt():
    collector = Collector()
    feed(collector, KEY_DOWN, VK_RIGHT_ALT, RIGHT_ALT_SCAN_CODE)
    assert _winkeyboard._altgr_right_alt_scan_code is not None

    _winkeyboard._reset_internal_state()
    assert _winkeyboard._altgr_right_alt_scan_code is None
    assert _winkeyboard.altgr_is_pressed is False
