import yaml
from dataclasses import dataclass


@dataclass
class MachineConfig:
    state: str
    tape: str
    head_position: int


@dataclass
class RunResult:
    accepted: bool
    reason: str
    final_tape: str
    steps: int
    history: list[MachineConfig]


class Tape:
    def __init__(self, input_string: str, blank_symbol: str):
        self.blank = blank_symbol
        self.tape = {}
        for i, char in enumerate(input_string):
            self.tape[i] = char

    def read(self, position: int) -> str:
        return self.tape.get(position, self.blank)

    def write(self, position: int, symbol: str):
        self.tape[position] = symbol

    def get_tape_string(self, head_position: int) -> str:
        if not self.tape:
            return self.blank

        all_indices = list(self.tape.keys()) + [head_position]
        min_index = min(all_indices)
        max_index = max(all_indices)

        tape_string = ""
        for i in range(min_index, max_index + 1):
            tape_string += self.read(i)

        return tape_string

    def get_tape_string_with_head(self, head_position: int) -> str:
        """Kafa konumunu köşeli parantez içinde göstererek şeridi döndürür.
        Örnek: head_position=1, şerit=1011 → 1[0]11
        """
        if not self.tape:
            return f"[{self.blank}]"

        all_indices = list(self.tape.keys()) + [head_position]
        min_index = min(all_indices)
        max_index = max(all_indices)

        tape_string = ""
        for i in range(min_index, max_index + 1):
            symbol = self.read(i)
            if i == head_position:
                tape_string += f"[{symbol}]"
            else:
                tape_string += symbol

        return tape_string


class SingleTapeTM:
    def __init__(self, states: list[str], input_alphabet: list[str],
                 tape_alphabet: list[str], transitions: dict,
                 initial_state: str, accept_states: list[str],
                 blank_symbol: str):
        self.states = states
        self.input_alphabet = input_alphabet
        self.tape_alphabet = tape_alphabet
        self.transitions = transitions
        self.initial_state = initial_state
        self.accept_states = accept_states
        self.blank_symbol = blank_symbol

    @classmethod
    def from_yaml(cls, file_path: str) -> 'SingleTapeTM':
        try:
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
        except Exception as e:
            raise ValueError(f"YAML dosyası okunurken hata oluştu: {e}")

        required_keys = ['states', 'input_alphabet', 'tape_alphabet',
                         'transitions', 'start_state', 'accept_states', 'blank']
        for key in required_keys:
            if key not in data:
                raise ValueError(f"YAML dosyasında '{key}' anahtarı eksik.")

        parsed_transitions = {}
        for rule in data['transitions']:
            state = rule['state']
            read_sym = str(rule['read'])

            if state not in parsed_transitions:
                parsed_transitions[state] = {}

            parsed_transitions[state][read_sym] = (
                str(rule['write']), rule['move'], rule['next']
            )

        return cls(
            states=data['states'],
            input_alphabet=data['input_alphabet'],
            tape_alphabet=data['tape_alphabet'],
            transitions=parsed_transitions,
            initial_state=data['start_state'],
            accept_states=data.get('accept_states', []),
            blank_symbol=data['blank']
        )

    def run(self, input_string: str, max_steps: int = 1000,
            verbose: bool = False) -> RunResult:
        tape = Tape(input_string, self.blank_symbol)
        current_state = self.initial_state
        head_position = 0
        steps = 0
        history = []

        while steps < max_steps:

            current_config = MachineConfig(
                state=current_state,
                tape=tape.get_tape_string(head_position),
                head_position=head_position
            )
            history.append(current_config)

            if current_state in self.accept_states:
                if verbose:
                    tape_with_head = tape.get_tape_string_with_head(head_position)
                    print(f"Adım {steps} | Durum: {current_state} | Şerit: {tape_with_head}")
                return RunResult(
                    accepted=True,
                    reason="accept",
                    final_tape=tape.get_tape_string(head_position),
                    steps=steps,
                    history=history
                )

            current_symbol = tape.read(head_position)
            state_rules = self.transitions.get(current_state, {})

            if current_symbol not in state_rules:
                return RunResult(
                    accepted=False,
                    reason="no_transition",
                    final_tape=tape.get_tape_string(head_position),
                    steps=steps,
                    history=history
                )

            rule = state_rules[current_symbol]
            new_symbol = rule[0]
            direction = rule[1]
            new_state = rule[2]

            # verbose=True ise kafa konumu köşeli parantez içinde gösterilir
            # Örnek: Adım 0 | Durum: q0 | Şerit: [1]011B | Hareket: R
            if verbose:
                tape_with_head = tape.get_tape_string_with_head(head_position)
                print(f"Adım {steps} | Durum: {current_state} | "
                      f"Şerit: {tape_with_head} | Hareket: {direction}")

            tape.write(head_position, new_symbol)

            if direction == 'R':
                head_position += 1
            elif direction == 'L':
                head_position -= 1

            current_state = new_state
            steps += 1

        return RunResult(
            accepted=False,
            reason="timeout",
            final_tape=tape.get_tape_string(head_position),
            steps=steps,
            history=history
        )


if __name__ == "__main__":

    try:
        tm = SingleTapeTM.from_yaml("machines/binary_increment.yaml")

        result = tm.run(input_string="1011", max_steps=1000, verbose=True)

        assert result.accepted is True, \
            "HATA: Makine kelimeyi kabul etmedi (False döndürdü)!"
        assert result.final_tape.strip("B") == "1100", \
            f"HATA: Şerit '1100' olmalıydı ama '{result.final_tape}' çıktı!"
        assert result.steps == 10, \
            f"HATA: Adım sayısı 10 olmalıydı ama {result.steps} adım sürdü!"
        assert len(result.history) == 11, \
            f"HATA: History uzunluğu 11 olmalıydı ama {len(result.history)} çıktı!"

        config = result.history[5]
        print(f"Durum: {config.state} | Şerit: {config.tape} | "
              f"Kafa Pozisyonu: {config.head_position}")


    except Exception as e:
        print(f"\n❌ TEST BAŞARISIZ: Bir hata oluştu -> {e}")
        