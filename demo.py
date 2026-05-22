import sys
import os
import time

_ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in [_ROOT, os.path.join(_ROOT, "turinglab")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tm_engine import SingleTapeTM

GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def banner(text: str):
    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}\n")


def subheader(text: str):
    print(f"\n{YELLOW}── {text} {'─' * max(0, 55 - len(text))}{RESET}")


def result_line(r):
    status = f"{GREEN}✅ KABUL{RESET}" if r.accepted else f"{RED}❌ RET{RESET}"
    tape_str = r.final_tape.strip("B") or "(boş)"
    print(f"\n{BOLD}Sonuç : {status}")
    print(f"Sebep : {r.reason}")
    print(f"Adım  : {r.steps}")
    print(f"Şerit : {tape_str}{RESET}")


def load(name: str) -> SingleTapeTM:
    path = os.path.join(_ROOT, "machines", f"{name}.yaml")
    return SingleTapeTM.from_yaml(path)


def demo_binary_increment():
    banner("DEMO 1 · Binary Increment  (1011 → 1100)")
    print("Makine : machines/binary_increment.yaml")
    print("Girdi  : 1011  (= 11 onluk)")
    print("Beklenen çıktı: 1100  (= 12)\n")
    time.sleep(0.3)
    tm = load("binary_increment")
    r  = tm.run("1011", max_steps=1000, verbose=True)
    result_line(r)


def demo_unary_to_binary():
    banner("DEMO 2 · Unary → Binary Çevirici")
    print("Makine : machines/unary_to_binary.yaml\n")
    time.sleep(0.3)
    tm = load("unary_to_binary")
    for girdi, onluk in [("1", 1), ("111", 3), ("1111", 4), ("11111", 5), ("1111111", 7)]:
        subheader(f"Girdi: {girdi!r}  (= {onluk} onluk)")
        r = tm.run(girdi, verbose=True)
        result_line(r)
        time.sleep(0.2)


def demo_binary_compare():
    banner("DEMO 3 · İkili Sayı Karşılaştırıcı  (A#B → A>B?)")
    print("Makine : machines/binary_compare.yaml\n")
    time.sleep(0.3)
    tm = load("binary_compare")
    for girdi, beklenen in [
        ("1100#1011", True),
        ("1000#0111", True),
        ("1011#1100", False),
        ("1010#1010", False),
        ("#",         False),
    ]:
        etiket = "KABUL bekleniyor" if beklenen else "RET bekleniyor"
        subheader(f"Girdi: {girdi!r}  →  {etiket}")
        r = tm.run(girdi, verbose=True)
        result_line(r)
        time.sleep(0.2)


def demo_string_copy():
    banner("DEMO 4 · Dizgi Kopyalayıcı  (abba → abba#abba)")
    print("Makine : machines/string_copy.yaml\n")
    time.sleep(0.3)
    tm = load("string_copy")
    for girdi in ["a", "bab", "abba"]:
        subheader(f"Girdi: {girdi!r}  →  beklenen: {girdi}#{girdi}")
        r = tm.run(girdi, verbose=True)
        result_line(r)
        time.sleep(0.2)


def demo_student_choice():
    banner("DEMO 5 · Bit Flipper  (0↔1 yer değiştirici)")
    print("Makine : machines/student_choice.yaml")
    print("Her '0' → '1', her '1' → '0' yapılır.\n")
    time.sleep(0.3)
    tm = load("student_choice")
    for girdi, beklenen in [
        ("1001", "0110"),
        ("111",  "000"),
        ("0000", "1111"),
        ("1010", "0101"),
        ("",     ""),
    ]:
        subheader(f"Girdi: {girdi!r}  →  beklenen: {beklenen!r}")
        r = tm.run(girdi, verbose=True)
        result_line(r)
        time.sleep(0.2)


DEMOS = {
    "1": ("Binary Increment",          demo_binary_increment),
    "2": ("Unary → Binary",            demo_unary_to_binary),
    "3": ("İkili Sayı Karşılaştırıcı", demo_binary_compare),
    "4": ("Dizgi Kopyalayıcı",         demo_string_copy),
    "5": ("Bit Flipper",               demo_student_choice),
    "0": ("Hepsini çalıştır",          None),
}


def main():
    banner("TuringLab — Canlı Demo")
    print("Hangi demo'yu çalıştırmak istiyorsunuz?\n")
    for k, (name, _) in DEMOS.items():
        print(f"  [{k}] {name}")
    print()
    choice = input("Seçiminiz (0-5): ").strip()
    if choice == "0":
        for k, (_, fn) in DEMOS.items():
            if fn:
                fn()
    elif choice in DEMOS and DEMOS[choice][1]:
        DEMOS[choice][1]()
    else:
        print("Geçersiz seçim.")
        sys.exit(1)
    banner("Demo tamamlandı ✅")


if __name__ == "__main__":
    main()