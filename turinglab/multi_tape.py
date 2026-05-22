"""
turinglab/multi_tape.py
-----------------------
Bonus A — Çok-Şeritli (Multi-Tape) Turing Makinesi Motoru.

Kullanım:
    from multi_tape import MultiTapeTM
    tm = MultiTapeTM.from_yaml("machines/binary_addition_mt.yaml")
    result = tm.run(["1011", "0101"])
    print(result.accepted, result.final_tapes)
"""

import yaml
from dataclasses import dataclass, field


@dataclass
class MultiTapeConfig:
    """Tek bir anlık konfigürasyonu temsil eder: durum, tüm şeritler, tüm kafa konumları."""
    state: str
    tapes: list[str]
    head_positions: list[int]


@dataclass
class MultiTapeRunResult:
    """MultiTapeTM.run() sonucunu taşır."""
    accepted: bool
    reason: str                    # "accept" | "no_transition" | "timeout"
    final_tapes: list[str]         # Her şeridin son hali (blank sıyrılmamış)
    steps: int
    history: list[MultiTapeConfig]


class MultiTape:
    """Tek bir şerit — dict[int, str] sparse yapı, negatif indeks güvenli."""

    def __init__(self, input_string: str, blank: str):
        self.blank = blank
        self._cells: dict[int, str] = {i: ch for i, ch in enumerate(input_string)}

    def read(self, pos: int) -> str:
        return self._cells.get(pos, self.blank)

    def write(self, pos: int, symbol: str) -> None:
        self._cells[pos] = symbol

    def as_string(self, head_pos: int) -> str:
        """Şeridi okunabilir string olarak döndürür."""
        if not self._cells:
            return self.blank
        indices = list(self._cells.keys()) + [head_pos]
        lo, hi = min(indices), max(indices)
        return "".join(self.read(i) for i in range(lo, hi + 1))

    def as_string_with_head(self, head_pos: int) -> str:
        """Kafa konumunu köşeli parantez içinde gösterir. Örnek: 10[1]1B"""
        if not self._cells:
            return f"[{self.blank}]"
        indices = list(self._cells.keys()) + [head_pos]
        lo, hi = min(indices), max(indices)
        parts = []
        for i in range(lo, hi + 1):
            sym = self.read(i)
            parts.append(f"[{sym}]" if i == head_pos else sym)
        return "".join(parts)


class MultiTapeTM:
    """
    k-şeritli deterministik Turing makinesi.

    YAML formatı (num_tapes: k ile):
        transitions:
          - state: q0
            read:  ["0", "B"]        # k sembol listesi
            write: ["0", "B"]        # k sembol listesi
            move:  ["R", "S"]        # k yön listesi  (R / L / S)
            next:  q1
    """

    def __init__(
        self,
        states: list[str],
        input_alphabet: list[str],
        tape_alphabet: list[str],
        num_tapes: int,
        transitions: dict,          # {state: {tuple(reads): (writes, moves, next_state)}}
        initial_state: str,
        accept_states: list[str],
        blank_symbol: str,
    ):
        self.states = states
        self.input_alphabet = input_alphabet
        self.tape_alphabet = tape_alphabet
        self.num_tapes = num_tapes
        self.transitions = transitions
        self.initial_state = initial_state
        self.accept_states = accept_states
        self.blank_symbol = blank_symbol

    # ------------------------------------------------------------------
    # YAML yükleyici
    # ------------------------------------------------------------------
    @classmethod
    def from_yaml(cls, file_path: str) -> "MultiTapeTM":
        """YAML dosyasından MultiTapeTM nesnesi oluşturur."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"YAML dosyası okunurken hata: {e}")

        required = [
            "states", "input_alphabet", "tape_alphabet",
            "num_tapes", "transitions", "start_state", "accept_states", "blank",
        ]
        for key in required:
            if key not in data:
                raise ValueError(f"YAML'da '{key}' anahtarı eksik.")

        k = data["num_tapes"]

        parsed: dict = {}
        for rule in data["transitions"]:
            state = rule["state"]
            reads = tuple(str(s) for s in rule["read"])   # k uzunluklu demet
            writes = [str(s) for s in rule["write"]]
            moves = rule["move"]                           # ["R","L","S",...]
            nxt = rule["next"]

            if len(reads) != k or len(writes) != k or len(moves) != k:
                raise ValueError(
                    f"Kural '{state}' için read/write/move listelerinin uzunluğu "
                    f"num_tapes={k} ile eşleşmiyor."
                )

            parsed.setdefault(state, {})[reads] = (writes, moves, nxt)

        return cls(
            states=data["states"],
            input_alphabet=data["input_alphabet"],
            tape_alphabet=data["tape_alphabet"],
            num_tapes=k,
            transitions=parsed,
            initial_state=data["start_state"],
            accept_states=data.get("accept_states", []),
            blank_symbol=data["blank"],
        )

    # ------------------------------------------------------------------
    # Çalıştırıcı
    # ------------------------------------------------------------------
    def run(
        self,
        inputs: list[str],
        max_steps: int = 5000,
        verbose: bool = False,
    ) -> MultiTapeRunResult:
        """
        Makineyi çalıştırır.

        Args:
            inputs: Her şerit için başlangıç dizgisi. len(inputs) == num_tapes olmalı.
                    Eksik şeritler boş kabul edilir.
            max_steps: Maksimum adım sayısı.
            verbose: Her adımı terminale yaz.

        Returns:
            MultiTapeRunResult nesnesi.
        """
        # Eksik şeritleri boş tamamla
        padded = list(inputs) + [""] * (self.num_tapes - len(inputs))
        tapes = [MultiTape(s, self.blank_symbol) for s in padded]
        heads = [0] * self.num_tapes
        current_state = self.initial_state
        steps = 0
        history: list[MultiTapeConfig] = []

        while steps < max_steps:
            # Anlık konfigürasyonu kaydet
            history.append(MultiTapeConfig(
                state=current_state,
                tapes=[tapes[i].as_string(heads[i]) for i in range(self.num_tapes)],
                head_positions=list(heads),
            ))

            # Kabul durumu kontrolü
            if current_state in self.accept_states:
                if verbose:
                    self._print_step(steps, current_state, tapes, heads, direction=None)
                return MultiTapeRunResult(
                    accepted=True,
                    reason="accept",
                    final_tapes=[tapes[i].as_string(heads[i]) for i in range(self.num_tapes)],
                    steps=steps,
                    history=history,
                )

            # Oku
            reads = tuple(tapes[i].read(heads[i]) for i in range(self.num_tapes))
            state_rules = self.transitions.get(current_state, {})

            if reads not in state_rules:
                return MultiTapeRunResult(
                    accepted=False,
                    reason="no_transition",
                    final_tapes=[tapes[i].as_string(heads[i]) for i in range(self.num_tapes)],
                    steps=steps,
                    history=history,
                )

            writes, moves, next_state = state_rules[reads]

            if verbose:
                self._print_step(steps, current_state, tapes, heads, moves)

            # Yaz ve kafaları hareket ettir
            for i in range(self.num_tapes):
                tapes[i].write(heads[i], writes[i])
                if moves[i] == "R":
                    heads[i] += 1
                elif moves[i] == "L":
                    heads[i] -= 1
                # "S" → yerinde kal

            current_state = next_state
            steps += 1

        return MultiTapeRunResult(
            accepted=False,
            reason="timeout",
            final_tapes=[tapes[i].as_string(heads[i]) for i in range(self.num_tapes)],
            steps=steps,
            history=history,
        )

    # ------------------------------------------------------------------
    # Yardımcı
    # ------------------------------------------------------------------
    def _print_step(
        self,
        step: int,
        state: str,
        tapes: list[MultiTape],
        heads: list[int],
        direction,
    ) -> None:
        """verbose modunda tek adımı yazdırır."""
        tape_parts = " | ".join(
            f"Şerit{i + 1}: {tapes[i].as_string_with_head(heads[i])}"
            for i in range(self.num_tapes)
        )
        dir_str = str(direction) if direction else "—"
        print(f"Adım {step:3d} | Durum: {state:12s} | {tape_parts} | Hareketler: {dir_str}")