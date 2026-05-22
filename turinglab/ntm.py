"""
turinglab/ntm.py
----------------
Bonus B — Non-Deterministik Turing Makinesi (NTM) Motoru.

BFS (Genişlik Öncelikli Arama) ile hesaplama ağacını gezinir.
DFS kullanılmaz çünkü sonsuz dallarda takılı kalır.

Kullanım:
    from ntm import NondeterministicTM
    tm = NondeterministicTM.from_yaml("machines/contains_01.yaml")
    result = tm.run("001101", max_depth=100, max_branches=1000)
    print(result.accepted)          # True
    print(result.accepting_paths)   # Kabul eden dalların konfigürasyon geçmişi
"""

import yaml
from collections import deque
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class NTMConfig:
    """Tek bir NTM anlık konfigürasyonu."""
    state: str
    tape: dict          # sparse dict {int: str}
    head: int


@dataclass
class NTMRunResult:
    """NondeterministicTM.run() sonucu."""
    accepted: bool
    reason: str                         # "accept" | "reject" | "timeout" | "branch_limit"
    steps: int                          # BFS katman sayısı
    branches_explored: int              # İncelenen toplam dal sayısı
    accepting_paths: list[list[str]]    # Kabul eden her dal için durum listesi


class NondeterministicTM:
    """
    Non-deterministik tek-şeritli Turing makinesi.

    YAML formatı — bir (state, read) çiftine birden fazla kural olabilir:
        transitions:
          - state: q0
            read:  "0"
            write: "X"
            move:  "R"
            next:  q1
          - state: q0      # aynı state+read, farklı eylem → non-determinizm
            read:  "0"
            write: "0"
            move:  "R"
            next:  q2
    """

    def __init__(
        self,
        states: list[str],
        input_alphabet: list[str],
        tape_alphabet: list[str],
        transitions: dict,          # {state: {read_sym: [(write, move, next), ...]}}
        initial_state: str,
        accept_states: list[str],
        blank_symbol: str,
    ):
        self.states = states
        self.input_alphabet = input_alphabet
        self.tape_alphabet = tape_alphabet
        self.transitions = transitions
        self.initial_state = initial_state
        self.accept_states = accept_states
        self.blank_symbol = blank_symbol

    # ------------------------------------------------------------------
    # YAML yükleyici
    # ------------------------------------------------------------------
    @classmethod
    def from_yaml(cls, file_path: str) -> "NondeterministicTM":
        """YAML dosyasından NondeterministicTM nesnesi oluşturur."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"YAML dosyası okunurken hata: {e}")

        required = [
            "states", "input_alphabet", "tape_alphabet",
            "transitions", "start_state", "accept_states", "blank",
        ]
        for key in required:
            if key not in data:
                raise ValueError(f"YAML'da '{key}' anahtarı eksik.")

        parsed: dict = {}
        for rule in data["transitions"]:
            state = rule["state"]
            read_sym = str(rule["read"])
            write_sym = str(rule["write"])
            move = rule["move"]
            nxt = rule["next"]

            parsed.setdefault(state, {}).setdefault(read_sym, [])
            parsed[state][read_sym].append((write_sym, move, nxt))

        return cls(
            states=data["states"],
            input_alphabet=data["input_alphabet"],
            tape_alphabet=data["tape_alphabet"],
            transitions=parsed,
            initial_state=data["start_state"],
            accept_states=data.get("accept_states", []),
            blank_symbol=data["blank"],
        )

    # ------------------------------------------------------------------
    # BFS çalıştırıcı
    # ------------------------------------------------------------------
    def run(
        self,
        input_string: str,
        max_depth: int = 200,
        max_branches: int = 10_000,
    ) -> NTMRunResult:
        """
        BFS ile tüm hesaplama dallarını gezinir.

        Args:
            input_string: Başlangıç şerit içeriği.
            max_depth: Maksimum BFS derinliği (adım sayısı).
            max_branches: Toplam incelenebilecek maksimum dal sayısı.

        Returns:
            NTMRunResult: Sonuç, incelenen dal sayısı ve kabul yolları.
        """
        # Her BFS düğümü: (tape_dict, head_pos, current_state, path)
        # path → [state0, state1, ...] (kabul yolu için)
        initial_tape = {i: ch for i, ch in enumerate(input_string)}
        initial_path = [self.initial_state]

        # queue elemanları: (tape, head, state, path, depth)
        queue: deque = deque()
        queue.append((initial_tape, 0, self.initial_state, initial_path, 0))

        accepting_paths: list[list[str]] = []
        branches_explored = 0
        max_depth_reached = 0

        while queue:
            tape, head, state, path, depth = queue.popleft()
            branches_explored += 1
            max_depth_reached = max(max_depth_reached, depth)

            # Dal limiti
            if branches_explored > max_branches:
                return NTMRunResult(
                    accepted=bool(accepting_paths),
                    reason="branch_limit",
                    steps=max_depth_reached,
                    branches_explored=branches_explored,
                    accepting_paths=accepting_paths,
                )

            # Derinlik limiti
            if depth > max_depth:
                continue  # Bu dalı terk et, diğerlerine devam et

            # Kabul durumu kontrolü
            if state in self.accept_states:
                accepting_paths.append(path)
                # İlk kabul eden yolu bulduk — diğer yolları da aramak istersen
                # continue diyebilirsin. Burada tüm kabul yollarını topluyoruz.
                continue

            # Okuma ve geçiş
            current_sym = tape.get(head, self.blank_symbol)
            choices = self.transitions.get(state, {}).get(current_sym, [])

            if not choices:
                # Bu dal reddedildi (dead end) — sessizce terk et
                continue

            for write_sym, move, next_state in choices:
                # Derin kopya — her dal bağımsız şeride sahip olmalı
                new_tape = dict(tape)
                new_tape[head] = write_sym

                new_head = head
                if move == "R":
                    new_head += 1
                elif move == "L":
                    new_head -= 1

                new_path = path + [next_state]
                queue.append((new_tape, new_head, next_state, new_path, depth + 1))

        if accepting_paths:
            return NTMRunResult(
                accepted=True,
                reason="accept",
                steps=max_depth_reached,
                branches_explored=branches_explored,
                accepting_paths=accepting_paths,
            )
        else:
            return NTMRunResult(
                accepted=False,
                reason="reject",
                steps=max_depth_reached,
                branches_explored=branches_explored,
                accepting_paths=[],
            )