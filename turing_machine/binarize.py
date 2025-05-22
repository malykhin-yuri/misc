import itertools
from collections.abc import Sequence
from typing import Literal

from turing_machine import TuringMachine


type Bit = Literal[0, 1]


class BinEncoder[ST, SYM]:
    def __init__(self, machine: TuringMachine[ST, SYM]):

        states = [machine.init_state]
        alphabet = [machine.empty_symbol]  # important: empty_symbol has index 0 => new empty 0 is ok
        seen_states = set()
        seen_alphabet = set()
        for (state, symbol), (new_state, new_symbol, _) in machine.rules.items():
            for st in state, new_state:
                if st not in seen_states:
                    states.append(st)
                    seen_states.add(st)

            for symb in symbol, new_symbol:
                if symb not in seen_alphabet:
                    alphabet.append(symb)
                    seen_alphabet.add(symb)

        self.orig_states = states
        self.alphabet = alphabet

        self.symbol_to_int = {symbol: index for index, symbol in enumerate(self.alphabet)}
        self.block_size = (len(self.alphabet) - 1).bit_length()
        self.formatter = '{0:0' + str(self.block_size) + 'b}'

        self.orig_machine = machine

    def _encode_symbol(self, symbol: SYM) -> tuple[Bit, ...]:
        index = self.symbol_to_int[symbol]
        return list(self.formatter.format(index))

    def _get_index(self, block: Sequence[Bit]) -> int:
        return int(''.join(map(str, block)), base=2)

    def _decode_symbol(self, block: Sequence[Bit]) -> SYM:
        index = self._get_index(block)
        return self.alphabet[index]

    def encode_input(self, tape: list[SYM]) -> list[Bit]:
        return sum((self._encode_symbol(s) for s in tape), start=[])

    def decode_output(self, tape: list[Bit]) -> list[SYM]:
        result = []
        start = 0
        b = self.block_size
        while start + b <= len(tape):
            block = tape[start:(start + b)]
            result.append(self._decode_symbol(block))
            start += b
        return result

    def encode_machine(self) -> TuringMachine[ST, Bit]:
        B = self.block_size
        init_state = ('regular', self.orig_machine.init_state)

        new_rules = {}
        # we have to store symbols in our states

        for orig_state in self.orig_states:
            # assume: orig machine in state = orig_state
            regular_state = ('regular', orig_state)  # head is on the start of some block

            read_start_state = ('read', orig_state, (0,) * B, 0)

            for bit in [0, 1]:
                new_rules[regular_state, bit] = (read_start_state, bit, 0)

            possible_data = list(itertools.product([0, 1], repeat=B))

            for index in range(B):  # this causes head move to position B and may create new empty symbols on the tape :(
                for data in possible_data:
                    read_curr_state = ('read', orig_state, data, index)
                    for bit in [0, 1]:
                        data_list = list(data)
                        data_list[index] = bit
                        read_next_state = ('read', orig_state, tuple(data_list), index + 1)  # here we "read"
                        new_rules[read_curr_state, bit] = (read_next_state, bit, +1)

            for data in possible_data:
                # assume: orig_symbol = current block = data
                # note that orig_state + orig_symbol define (new_state, new_symbol, delta)
                read_finish_state = ('read', orig_state, data, B)

                if self._get_index(data) >= len(self.alphabet):
                    continue

                orig_symbol = self._decode_symbol(data)
                orig_key = orig_state, orig_symbol
                if orig_key not in self.orig_machine.rules:
                    continue

                new_orig_state, new_orig_symbol, delta = self.orig_machine.rules[orig_key]

                write_start_state = ('write', new_orig_state, data, B-1)  # here we "change state"!
                for bit in [0, 1]:
                    new_rules[read_finish_state, bit] = (write_start_state, bit, -1)

                for index in range(B-1, 0, -1):
                    for bit in [0, 1]:
                        write_curr_state = ('write', new_orig_state, data, index)
                        write_next_state = ('write', new_orig_state, data, index - 1)
                        new_rules[write_curr_state, bit] = (write_next_state, data[index], -1)  # here we "write" (backwards)

                write_finish_state = ('write', new_orig_state, data, 0)
                move_start_state = ('move', new_orig_state, delta, 0)

                for index in range(B):
                    for bit in [0, 1]:
                        move_curr_state = ('move', new_orig_state, delta, index)
                        move_next_state = ('move', new_orig_state, delta, index + 1)
                        new_rules[move_curr_state, bit] = (move_next_state, bit, delta)  # here we "move"

                move_finish_state = ('move', new_orig_state, delta, B)
                for bit in [0, 1]:
                    new_regular_state = ('regular', new_orig_state)
                    new_rules[move_finish_state, bit] = (new_regular_state, bit, 0)

        return TuringMachine(rules=new_rules, init_state=init_state, empty_symbol=0)
