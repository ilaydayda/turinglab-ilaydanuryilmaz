import pytest
from turinglab.tm_engine import SingleTapeTM

def test_tm1_unary_to_binary():
    tm = SingleTapeTM.from_yaml("machines/unary_to_binary.yaml")
    
    # 2 Kabul ve 1 Kenar Durum
    accept_cases = [
        ("111",  "11"),
        ("1111", "100"),
        ("",     "0"),   # Kenar durum: boş şerit
    ]
    for inp, expected_bin in accept_cases:
        result = tm.run(inp)
        final_str = result.final_tape.replace("B", "").lstrip("0") or "0"
        assert result.accepted is True, f"'{inp}' kabul edilmeliydi."
        assert final_str == expected_bin, f"Beklenen {expected_bin}, alınan {final_str}"

    # 2 Ret Durumu (Geçersiz karakterler içeren girdiler)
    reject_cases = ["11a", "xyz"]
    for inp in reject_cases:
        result = tm.run(inp)
        assert result.accepted is False, f"Geçersiz girdi '{inp}' reddedilmeliydi."

def test_tm2_binary_compare():
    tm = SingleTapeTM.from_yaml("machines/binary_compare.yaml")
    
    # 2 Kabul Durumu (Sol taraf > Sağ taraf)
    accept_cases = [
        "1100#1011",   # 12 > 11
        "1000#0111",   # 8 > 7 
    ]
    for inp in accept_cases:
        result = tm.run(inp)
        assert result.accepted is True, f"'{inp}' kabul edilmeliydi (Sol > Sağ)."

    # 2 Ret Durumu ve 1 Kenar Durum
    reject_cases = [
        "1011#1100",   # 11 < 12 (Ret)
        "1010#1010",   # 10 = 10 (Eşitlik reddedilir)
        "#",           # Kenar durum: boş sayılar eşittir, reddedilir
    ]
    for inp in reject_cases:
        result = tm.run(inp)
        assert result.accepted is False, f"'{inp}' reddedilmeliydi."

def test_tm3_string_copy():
    tm = SingleTapeTM.from_yaml("machines/string_copy.yaml")
    
    # 2 Kabul ve 1 Kenar Durum
    accept_cases = [
        ("abba", "abba#abba"),
        ("bab",  "bab#bab"),
        ("",     "#")  # Kenar durum: boş kelime kopyalanırsa sadece # kalır
    ]
    for inp, expected_tape in accept_cases:
        result = tm.run(inp)
        final_str = result.final_tape.replace("B", "")
        assert result.accepted is True, f"'{inp}' kopyalanıp kabul edilmeliydi."
        assert final_str == expected_tape, f"Beklenen {expected_tape}, alınan {final_str}"

    # 2 Ret Durumu (Yanlış alfabe veya kural dışı sembol kullanımı)
    reject_cases = ["ab1a", "a#b"] 
    for inp in reject_cases:
        result = tm.run(inp)
        assert result.accepted is False, f"Geçersiz karakter içeren '{inp}' reddedilmeliydi."

def test_tm4_student_choice():
    """
    TM-4 Öğrenci Seçimi: Bit Flipper (0'ları 1, 1'leri 0 yapar)
    """
    tm = SingleTapeTM.from_yaml("machines/student_choice.yaml")
    
    # 2 Kabul ve 1 Kenar Durum
    accept_cases = [
        ("1001", "0110"),
        ("111",  "000"),
        ("",     "")     # Kenar durum: boş şerit aynı kalır
    ]
    for inp, expected_tape in accept_cases:
        result = tm.run(inp)
        final_str = result.final_tape.replace("B", "")
        assert result.accepted is True, f"'{inp}' işlenip kabul edilmeliydi."
        assert final_str == expected_tape, f"Beklenen {expected_tape}, alınan {final_str}"

    # 2 Ret Durumu (Alfabede olmayan harfler)
    reject_cases = ["10a1", "x"] 
    for inp in reject_cases:
        result = tm.run(inp)
        assert result.accepted is False, f"Geçersiz girdi '{inp}' reddedilmeliydi."