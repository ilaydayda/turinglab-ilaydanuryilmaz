"""
tests/test_tm_engine.py
-----------------------
Turing Makinesi Motoru için test paketi — tam 8 test fonksiyonu.
"""

import os
import sys
import tempfile
import pytest

# tm_engine.py'nin bulunduğu turinglab/ klasörünü path'e ekle
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_TURINGLAB = os.path.join(_ROOT, "turinglab")
for _p in [_ROOT, _TURINGLAB]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tm_engine import SingleTapeTM

MACHINES_DIR = os.path.join(os.path.dirname(__file__), "..", "machines")


def load(name: str) -> SingleTapeTM:
    return SingleTapeTM.from_yaml(os.path.join(MACHINES_DIR, f"{name}.yaml"))


def make_unary_increment() -> SingleTapeTM:
    """Unary increment: şeridin sonuna bir '1' ekler."""
    return SingleTapeTM(
        states=["q0", "q_accept"],
        input_alphabet=["1"],
        tape_alphabet=["1", "B"],
        transitions={
            "q0": {"1": ("1", "R", "q0"), "B": ("1", "R", "q_accept")},
        },
        initial_state="q0",
        accept_states=["q_accept"],
        blank_symbol="B",
    )


def make_even_a() -> SingleTapeTM:
    """Çift sayıda 'a' içeren stringleri kabul eder."""
    return SingleTapeTM(
        states=["q_even", "q_odd", "q_accept"],
        input_alphabet=["a", "b"],
        tape_alphabet=["a", "b", "B"],
        transitions={
            "q_even": {"a": ("a", "R", "q_odd"),  "b": ("b", "R", "q_even"), "B": ("B", "R", "q_accept")},
            "q_odd":  {"a": ("a", "R", "q_even"), "b": ("b", "R", "q_odd"),  "B": ("B", "R", "q_odd")},
        },
        initial_state="q_even",
        accept_states=["q_accept"],
        blank_symbol="B",
    )


def test_binary_increment_five_inputs():
    """binary_increment: 5 farklı girdi için doğru sonuç."""
    tm = load("binary_increment")
    assert tm.run("1011").final_tape.strip("B") == "1100"
    assert tm.run("0").final_tape.strip("B")    == "1"
    assert tm.run("10").final_tape.strip("B")   == "11"
    assert tm.run("100").final_tape.strip("B")  == "101"
    assert tm.run("1010").final_tape.strip("B") == "1011"


def test_unary_increment_five_inputs():
    """unary_increment: 5 farklı girdi için doğru '1' sayısı."""
    tm = make_unary_increment()
    assert tm.run("").final_tape.strip("B").count("1")      == 1
    assert tm.run("1").final_tape.strip("B").count("1")     == 2
    assert tm.run("11").final_tape.strip("B").count("1")    == 3
    assert tm.run("111").final_tape.strip("B").count("1")   == 4
    assert tm.run("11111").final_tape.strip("B").count("1") == 6


def test_even_a_five_inputs():
    """even_a: kabul ve ret durumları 5 girdi ile doğrulanır."""
    tm = make_even_a()
    assert tm.run("").accepted        is True
    assert tm.run("aabb").accepted    is True
    assert tm.run("aabbaab").accepted is True
    assert tm.run("ab").accepted      is False
    assert tm.run("aaab").accepted    is False


def test_history_records_every_step():
    """history listesi uzunluğu steps + 1 olmalı; ilk kayıt başlangıç konfigürasyonu."""
    r = load("binary_increment").run("1011")
    assert len(r.history) == r.steps + 1
    assert r.history[0].state == "q0"
    assert r.history[0].head_position == 0


def test_timeout():
    """max_steps aşılınca accepted=False, reason='timeout', steps==max_steps."""
    tm = SingleTapeTM(
        states=["q0"],
        input_alphabet=["a"],
        tape_alphabet=["a", "B"],
        transitions={"q0": {"a": ("a", "R", "q0"), "B": ("B", "R", "q0")}},
        initial_state="q0",
        accept_states=["q_accept"],
        blank_symbol="B",
    )
    r = tm.run("aaa", max_steps=50)
    assert r.accepted is False
    assert r.reason == "timeout"
    assert r.steps == 50


def test_no_transition():
    """Geçiş kuralı olmayan durumda accepted=False, reason='no_transition'."""
    tm = SingleTapeTM(
        states=["q0", "q_accept"],
        input_alphabet=["a"],
        tape_alphabet=["a", "B"],
        transitions={"q0": {"a": ("a", "R", "q0")}},
        initial_state="q0",
        accept_states=["q_accept"],
        blank_symbol="B",
    )
    r = tm.run("a")
    assert r.accepted is False
    assert r.reason == "no_transition"


def test_invalid_yaml_raises_value_error():
    """Zorunlu anahtar eksik YAML ve var olmayan dosya → ValueError."""
    import yaml
    bad = {"states": ["q0"], "blank": "B"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(bad, f)
        path = f.name
    try:
        with pytest.raises(ValueError):
            SingleTapeTM.from_yaml(path)
    finally:
        os.unlink(path)

    with pytest.raises(ValueError):
        SingleTapeTM.from_yaml("machines/nonexistent.yaml")


def test_verbose_output(capsys):
    """verbose=True: her adım satırı kafa konumuyla, kabul durumu da çıktıda görünmeli."""
    load("binary_increment").run("1011", verbose=True)
    out = capsys.readouterr().out
    assert "Adım 0" in out
    assert "q0" in out
    assert "q_accept" in out
    assert any("[" in line and "]" in line for line in out.splitlines())