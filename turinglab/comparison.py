"""
turinglab/comparison.py
-----------------------
Bonus C — Karşılaştırmalı Performans Analizi

Aynı dil (L = {w | w '01' alt-dizgisi içerir}) için üç farklı yaklaşımı
karşılaştırır:
  1. SingleTapeTM  — tek şeritli deterministik TM
  2. MultiTapeTM   — 2-şeritli TM (kopya + tarama ayrı şeritlerde)
  3. NondeterministicTM — NTM (BFS ile)

Her girdi uzunluğu için adım sayılarını ölçer ve matplotlib ile grafik üretir.
Çıktı: docs/comparison.png

Çalıştırmak için (proje kökünden):
    python turinglab/comparison.py
"""

import sys
import os
import matplotlib
matplotlib.use("Agg")           # GUI olmadan PNG üret
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# turinglab/ paketini path'e ekle
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from tm_engine import SingleTapeTM
from multi_tape import MultiTapeTM
from ntm import NondeterministicTM


# ──────────────────────────────────────────────────────────────────────
# Yardımcı: en kötü durum girdi üret
# L = {w | w '01' içerir}
# En kötü durum: '01' en sonda (111...101) → makine tüm şeridi taramalı
# ──────────────────────────────────────────────────────────────────────
def worst_case_input(n: int) -> str:
    """n uzunlukta en kötü durum: 111...101 (son 2 karakter '01')."""
    if n < 2:
        return "01"[:n] if n > 0 else "0"
    return "1" * (n - 2) + "01"


# ──────────────────────────────────────────────────────────────────────
# Makine 1: Tek-şeritli deterministik TM (contains_01 — YAML tanımı)
# İnşa: doğrudan kod ile (YAML dosyasına bağımlı olmadan taşınabilir)
# ──────────────────────────────────────────────────────────────────────
def build_single_tape_tm() -> SingleTapeTM:
    """'01' içeriyor mu?' sorusunu cevaplayan tek-şeritli DTM."""
    transitions = {
        "q0": {
            "0": ("0", "R", "q1"),   # '0' gördük, q1'e geç
            "1": ("1", "R", "q0"),   # '1' gördük, devam
            "B": ("B", "S", "q_reject"),  # bitti, bulamadık
        },
        "q1": {
            "1": ("1", "R", "q_accept"),  # '01' tamam!
            "0": ("0", "R", "q1"),        # ardışık '0', hâlâ umut var
            "B": ("B", "S", "q_reject"),  # bitti
        },
        "q_reject": {},
    }
    return SingleTapeTM(
        states=["q0", "q1", "q_accept", "q_reject"],
        input_alphabet=["0", "1"],
        tape_alphabet=["0", "1", "B"],
        transitions=transitions,
        initial_state="q0",
        accept_states=["q_accept"],
        blank_symbol="B",
    )


# ──────────────────────────────────────────────────────────────────────
# Makine 2: 2-şeritli TM
# Şerit 1: orijinal girdi (salt-okunur gibi kullanılır)
# Şerit 2: tarama için yardımcı — aynı mantık ama ayrı şerit
# Adım sayısı açısından tek-şeritli ile özdeş bu basit dil için;
# ancak daha karmaşık dillerde (palindrom vb.) fark ortaya çıkar.
# ──────────────────────────────────────────────────────────────────────
def build_multi_tape_tm() -> MultiTapeTM:
    """2-şeritli '01 içeriyor mu?' TM."""
    transitions = {
        "q0": {
            ("0", "B"): (["0", "0"], ["R", "R"], "q1"),
            ("1", "B"): (["1", "1"], ["R", "R"], "q0"),
            ("B", "B"): (["B", "B"], ["S", "S"], "q_reject"),
        },
        "q1": {
            ("1", "1"): (["1", "1"], ["R", "R"], "q_accept"),
            ("0", "0"): (["0", "0"], ["R", "R"], "q1"),
            ("B", "B"): (["B", "B"], ["S", "S"], "q_reject"),
        },
        "q_reject": {},
    }
    return MultiTapeTM(
        states=["q0", "q1", "q_accept", "q_reject"],
        input_alphabet=["0", "1"],
        tape_alphabet=["0", "1", "B"],
        num_tapes=2,
        transitions=transitions,
        initial_state="q0",
        accept_states=["q_accept"],
        blank_symbol="B",
    )


# ──────────────────────────────────────────────────────────────────────
# Makine 3: NTM (contains_01.yaml ile aynı mantık — kod içi)
# ──────────────────────────────────────────────────────────────────────
def build_ntm() -> NondeterministicTM:
    """'01 içeriyor mu?' NTM."""
    transitions = {
        "q0": {
            "0": [("0", "R", "q0"), ("0", "R", "q1")],   # non-deterministik dal
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


# ──────────────────────────────────────────────────────────────────────
# Ölçüm
# ──────────────────────────────────────────────────────────────────────
def measure(lengths: list[int]):
    """Her uzunluk için 3 makinenin adım sayılarını ölç."""
    dtm = build_single_tape_tm()
    mtm = build_multi_tape_tm()
    ntm = build_ntm()

    dtm_steps, mtm_steps, ntm_steps = [], [], []

    for n in lengths:
        w = worst_case_input(n)

        r_dtm = dtm.run(w, max_steps=50_000)
        dtm_steps.append(r_dtm.steps)

        r_mtm = mtm.run([w, ""], max_steps=50_000)
        mtm_steps.append(r_mtm.steps)

        r_ntm = ntm.run(w, max_depth=n + 10, max_branches=50_000)
        ntm_steps.append(r_ntm.steps)

    return dtm_steps, mtm_steps, ntm_steps


# ──────────────────────────────────────────────────────────────────────
# Grafik
# ──────────────────────────────────────────────────────────────────────
def plot(lengths, dtm_steps, mtm_steps, ntm_steps, output_path: str):
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(lengths, dtm_steps, marker="o", linewidth=2,
            label="DTM — Tek Şeritli", color="#2196F3")
    ax.plot(lengths, mtm_steps, marker="s", linewidth=2,
            label="MTM — 2 Şeritli",   color="#4CAF50", linestyle="--")
    ax.plot(lengths, ntm_steps, marker="^", linewidth=2,
            label="NTM — BFS Derinliği", color="#FF5722", linestyle=":")

    ax.set_xlabel("Girdi Uzunluğu (n)", fontsize=12)
    ax.set_ylabel("Adım Sayısı", fontsize=12)
    ax.set_title(
        "L = {w | w '01' alt-dizgisini içerir}\n"
        "DTM · MTM · NTM Karşılaştırmalı Adım Analizi",
        fontsize=13, fontweight="bold"
    )
    ax.legend(fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"✅ Grafik kaydedildi: {output_path}")


# ──────────────────────────────────────────────────────────────────────
# Ana akış
# ──────────────────────────────────────────────────────────────────────
def main():
    lengths = list(range(2, 31))        # n = 2 … 30
    print("⏳ Ölçümler yapılıyor...")
    dtm_steps, mtm_steps, ntm_steps = measure(lengths)

    print("\n{'n':>4} | {'DTM':>6} | {'MTM':>6} | {'NTM':>6}")
    print("-" * 30)
    for n, d, m, t in zip(lengths, dtm_steps, mtm_steps, ntm_steps):
        print(f"{n:>4} | {d:>6} | {m:>6} | {t:>6}")

    # Çıktı yolu — proje kökünde çalıştırıldığı varsayılır
    out = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "comparison.png"
    )
    plot(lengths, dtm_steps, mtm_steps, ntm_steps, out)


if __name__ == "__main__":
    main()