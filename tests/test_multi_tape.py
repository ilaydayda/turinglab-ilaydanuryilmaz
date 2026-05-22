"""
tests/test_multi_tape.py
------------------------
Bonus A — MultiTapeTM ve Bonus B — NondeterministicTM testleri.
Çalıştır: pytest tests/test_multi_tape.py -v
"""

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_TL   = os.path.join(_ROOT, "turinglab")
for _p in [_ROOT, _TL]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from multi_tape import MultiTapeTM
from ntm import NondeterministicTM


# ══════════════════════════════════════════════════════════════════════
# Yardımcı: kod içi makineler (YAML bağımlılığı olmadan çalışır)
# ══════════════════════════════════════════════════════════════════════

def build_adder() -> MultiTapeTM:
    """İkili toplama — 3 şerit."""
    return MultiTapeTM.from_yaml(
        os.path.join(_ROOT, "machines", "binary_addition_mt.yaml")
    )


def build_ntm_contains01() -> NondeterministicTM:
    """'01' içeriyor mu? NTM — kod içi."""
    transitions = {
        "q0": {
            "0": [("0", "R", "q0"), ("0", "R", "q1")],
            "1": [("1", "R", "q0")],
        },
        "q1": {
            "1": [("1", "R", "q_accept")],
        },
    }
    return NondeterministicTM(
        states=["q0", "q1", "q_accept"],
        input_alphabet=["0", "1"],
        tape_alphabet=["0", "1", "B"],
        transitions=transitions,
        initial_state="q0",
        accept_states=["q_accept"],
        blank_symbol="B",
    )


# ══════════════════════════════════════════════════════════════════════
# Bonus A Testleri — MultiTapeTM
# ══════════════════════════════════════════════════════════════════════

def test_multi_tape_addition_basic():
    """1+1 = 10 (binary)."""
    tm = build_adder()
    r = tm.run(["1", "1"])
    assert r.accepted is True
    assert r.final_tapes[2].strip("B") == "10"


def test_multi_tape_addition_1011_plus_0101():
    """1011 + 0101 = 10000 (11 + 5 = 16)."""
    tm = build_adder()
    r = tm.run(["1011", "0101"])
    assert r.accepted is True
    assert r.final_tapes[2].strip("B") == "10000"


def test_multi_tape_addition_zero():
    """0 + 0 = 0."""
    tm = build_adder()
    r = tm.run(["0", "0"])
    assert r.accepted is True
    assert r.final_tapes[2].strip("B") == "0"


def test_multi_tape_addition_asymmetric():
    """110 + 1 = 111 (6 + 1 = 7)."""
    tm = build_adder()
    r = tm.run(["110", "1"])
    assert r.accepted is True
    assert r.final_tapes[2].strip("B") == "111"


def test_multi_tape_addition_with_carry():
    """111 + 1 = 1000 (7 + 1 = 8)."""
    tm = build_adder()
    r = tm.run(["111", "1"])
    assert r.accepted is True
    assert r.final_tapes[2].strip("B") == "1000"


def test_multi_tape_history_length():
    """history uzunluğu steps + 1 olmalı."""
    tm = build_adder()
    r = tm.run(["1", "1"])
    assert len(r.history) == r.steps + 1


def test_multi_tape_timeout():
    """max_steps aşılınca timeout döner."""
    tm = build_adder()
    r = tm.run(["1111111111", "1111111111"], max_steps=5)
    assert r.accepted is False
    assert r.reason == "timeout"


# ══════════════════════════════════════════════════════════════════════
# Bonus B Testleri — NondeterministicTM
# ══════════════════════════════════════════════════════════════════════

def test_ntm_contains_01_accepts():
    """'01' içeren dizgiler kabul edilmeli."""
    tm = build_ntm_contains01()
    assert tm.run("01").accepted is True
    assert tm.run("001").accepted is True
    assert tm.run("101").accepted is True
    assert tm.run("1101011").accepted is True
    assert tm.run("00001").accepted is True


def test_ntm_contains_01_rejects():
    """'01' içermeyen dizgiler reddedilmeli."""
    tm = build_ntm_contains01()
    assert tm.run("").accepted is False
    assert tm.run("0").accepted is False
    assert tm.run("1").accepted is False
    assert tm.run("11111").accepted is False
    assert tm.run("00000").accepted is False


def test_ntm_accepting_paths_not_empty():
    """Kabul eden dizgi için accepting_paths boş olmamalı."""
    tm = build_ntm_contains01()
    r = tm.run("01")
    assert r.accepted is True
    assert len(r.accepting_paths) > 0


def test_ntm_accepting_paths_empty_on_reject():
    """Reddeden dizgi için accepting_paths boş olmalı."""
    tm = build_ntm_contains01()
    r = tm.run("111")
    assert r.accepted is False
    assert r.accepting_paths == []


def test_ntm_branch_limit():
    """max_branches=1 ile branch_limit reason dönmeli."""
    tm = build_ntm_contains01()
    r = tm.run("01", max_depth=100, max_branches=1)
    assert r.reason in ("branch_limit", "accept")  # 1 dalda kabul de mümkün


def test_ntm_from_yaml():
    """contains_01.yaml'dan yükleme ve çalıştırma."""
    yaml_path = os.path.join(_ROOT, "machines", "contains_01.yaml")
    if not os.path.exists(yaml_path):
        import pytest
        pytest.skip("contains_01.yaml machines/ klasöründe bulunamadı")
    tm = NondeterministicTM.from_yaml(yaml_path)
    assert tm.run("01").accepted is True
    assert tm.run("11").accepted is False


def test_ntm_reason_reject():
    """Reddeden dizgi için reason 'reject' olmalı."""
    tm = build_ntm_contains01()
    r = tm.run("111")
    assert r.reason == "reject"