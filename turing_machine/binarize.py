import itertools
from collections.abc import Sequence
from typing import Literal, Any
from enum import Enum

from turing_machine import TuringMachine


class BinStateGroup(Enum):
    REGULAR = 1
    READ = 2
    WRITE = 3
    MOVE = 4

type DeltaType = Literal[-1, 0, 1]
type Bit = Literal[0, 1]
type BinState[ST_] = tuple[BinStateGroup, ST_, Any]


class BinEncoder[ST, SYM]:

    def __init__(self, machine: TuringMachine[ST, SYM]) -> None:
        states = [machine.init_state]
        alphabet = [machine.empty_symbol]  # important: empty_symbol has index 0 => new empty 0 is ok
        seen_states = set(states)
        seen_alphabet = set(alphabet)
        for (state, symbol), (new_state, new_symbol, _) in machine.rules.items():
            if symbol is None:
                raise NotImplementedError
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

        self.symbol_index = {symbol: index for index, symbol in enumerate(self.alphabet)}
        self.block_size = (len(self.alphabet) - 1).bit_length()
        self.formatter = '{0:0' + str(self.block_size) + 'b}'

        self.orig_machine = machine

    def _encode_symbol(self, symbol: SYM) -> list[Bit]:
        index = self.symbol_index[symbol]
        return list(map(int, self.formatter.format(index)))  # type: ignore

    def _decode_symbol(self, block: Sequence[Bit]) -> SYM:
        index = int(''.join(map(str, block)), base=2)
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

    def encode_machine(self) -> TuringMachine[BinState[ST], Bit]:
        G = BinStateGroup
        B = self.block_size
        bits: list[Bit] = [0, 1]
        deltas: list[DeltaType] = [-1, 0, 1]

        init_state: BinState[ST] = (G.REGULAR, self.orig_machine.init_state, None)
        new_rules: dict[tuple[BinState[ST], Bit], tuple[BinState[ST], Bit, DeltaType]] = {}

        def switch_internal_state(state1: BinState[ST], state2: BinState[ST], delta: DeltaType = 0) -> None:
            for bit in bits:
                new_rules[state1, bit] = (state2, bit, delta)

        # start
        for orig_state in self.orig_states:
            regular_state = (G.REGULAR, orig_state, None)  # head is on the start of some block
            read_start_state = (G.READ, orig_state, ())  # () = data already read
            switch_internal_state(regular_state, read_start_state)

        # read + change state + write
        seen_move = set()
        for (orig_state, orig_symbol), (new_orig_state, new_orig_symbol, orig_delta) in self.orig_machine.rules.items():
            bin_symbol = tuple(self._encode_symbol(orig_symbol))
            delta: DeltaType
            # reading symbol orig_symbol
            for index in range(B):
                read_curr_state = (G.READ, orig_state, bin_symbol[:index])
                read_next_state = (G.READ, orig_state, bin_symbol[:(index+1)])
                delta = +1 if index < B-1 else 0
                bit = bin_symbol[index]
                new_rules[read_curr_state, bit] = (read_next_state, bit, delta)  # here we "read"

            read_finish_state = (G.READ, orig_state, bin_symbol)  # head is on the end of the block
            to_write = tuple(self._encode_symbol(new_orig_symbol)) if new_orig_symbol is not None else (None,) * B
            to_move = orig_delta * B

            # we should remember delta in write state to disambiguate states
            write_start_state = (G.WRITE, new_orig_state, (to_write, to_move))
            switch_internal_state(read_finish_state, write_start_state)  # here we "change state"

            while len(to_write) > 0:
                write_curr_state = (G.WRITE, new_orig_state, (to_write, to_move))
                next_to_write = to_write[:-1]
                write_next_state = (G.WRITE, new_orig_state, (next_to_write, to_move))
                delta = -1 if len(to_write) > 1 else 0
                for bit in bits:
                    new_rules[write_curr_state, bit] = (write_next_state, to_write[-1], delta)  # here we "write" (backwards)
                to_write = next_to_write

            write_finish_state = (G.WRITE, new_orig_state, ((), to_move))
            move_start_state = (G.MOVE, new_orig_state, to_move)
            switch_internal_state(write_finish_state, move_start_state)
            seen_move.add((new_orig_state, to_move))

        # move
        for orig_state, to_move in seen_move:
            while to_move != 0:
                delta = 1 if to_move > 0 else -1
                move_curr_state = (G.MOVE, orig_state, to_move)
                next_to_move = to_move - delta
                move_next_state = (G.MOVE, orig_state, next_to_move)
                for bit in bits:
                    new_rules[move_curr_state, bit] = (move_next_state, bit, delta)  # here we "move"
                to_move = next_to_move

            move_finish_state = (G.MOVE, orig_state, 0)
            new_regular_state = (G.REGULAR, orig_state, None)
            switch_internal_state(move_finish_state, new_regular_state)

        return TuringMachine(rules=new_rules, init_state=init_state, empty_symbol=0)
