import pytest
from turinglab.tm_engine import SingleTapeTM

def test_tm1_unary_to_binary():
    tm = SingleTapeTM.from_yaml("machines/unary_to_binary.yaml")
    test_cases = [
        ("111",  "11"),
        ("1111", "100"),
        ("1",    "1"),
        ("11",   "10"),
        ("",     "0"),   # kenar durum
    ]
    for inp, expected_bin in test_cases:
        result = tm.run(inp)
        final_str = result.final_tape.strip("B").lstrip("0") or "0"
        assert result.accepted is True
        assert final_str == expected_bin

def test_tm2_binary_compare():
    tm = SingleTapeTM.from_yaml("machines/binary_compare.yaml")
    
    # Sol taraf > Sağ taraf ise kabul
    test_cases = [
        ("1100#1011", True),   # 12 > 11 (Kabul)
        ("1000#0111", True),   # 8 > 7   (Kabul)
        ("1011#1100", False),  # 11 < 12 (Ret)
        ("1010#1010", False),  # 10 = 10 (Ret - eşitlik ret edilir)
        ("#", False)           # Kenar durum: boş sayılar eşittir, ret edilir
    ]
    for inp, expected in test_cases:
        result = tm.run(inp)
        assert result.accepted == expected

def test_tm3_string_copy():
    tm = SingleTapeTM.from_yaml("machines/string_copy.yaml")
    
    test_cases = [
        ("abba", "abba#abba"),
        ("a", "a#a"),
        ("bab", "bab#bab"),
        ("bb", "bb#bb"),
        ("", "#") # Kenar durum: boş kelime kopyalanırsa sadece # kalır
    ]
    for inp, expected_tape in test_cases:
        result = tm.run(inp)
        final_str = result.final_tape.replace("B", "")
        assert result.accepted is True
        assert final_str == expected_tape
