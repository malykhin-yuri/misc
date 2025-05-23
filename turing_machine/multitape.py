"""
Multitape Turing Machine.
This module also will provide wrapper to emulate MTM by a regular TM
"""

from collections.abc import Sequence, Iterable
from copy import deepcopy
from typing import Literal
import itertools

from turing_machine import TuringMachine

type DeltaType = Literal[-1, 0, 1]
type HeadsData[SYM] = tuple[SYM, ...]
type RulesType[ST, SYM] = dict[tuple[ST, HeadsData[SYM]], tuple[ST, HeadsData[SYM], tuple[DeltaType, ...]]]
type PartialData[SYM] = dict[int, SYM]
type PartialDelta = dict[int, DeltaType]

# TODO: unify with patches.py
def patch_partial[ST, SYM](
        alphabet: Iterable[SYM], tapes_count: int, partial_rules: dict[ST, Sequence[tuple[PartialData[SYM], ST, PartialData[SYM], PartialDelta]]]
    ) -> RulesType[ST, SYM]:

    alphabet_list = list(alphabet)
    result = {}
    for state, state_rules in partial_rules.items():
        for read_data, new_state, write_data, deltas in state_rules:
            full_deltas = tuple(deltas.get(index, 0) for index in range(tapes_count))

            # read_data is partial dict, fill in gaps
            for missing_tuple in itertools.product(alphabet_list, repeat=tapes_count - len(read_data)):
                missing = list(missing_tuple)
                read_full_data: list[SYM] = []
                for index in range(tapes_count):
                    if index in read_data:
                        read_full_data.append(read_data[index])
                    else:
                        read_full_data.append(missing.pop(0))
                write_full_data = tuple(write_data.get(index, read_full_data[index]) for index in range(tapes_count))
                result[state, tuple(read_full_data)] = (new_state, write_full_data, full_deltas)

    return result


class MultitapeTuringMachine[ST, SYM]:
    """
    Enriched Turing Machine: allows multiple tapes.
    """

    tapes: list[list[SYM]]
    heads: list[int]

    def __init__(self,
            tapes_count: int,
            rules: RulesType[ST, SYM],
            init_state: ST,
            empty_symbol: SYM,
        ):
        self._assert_rules(tapes_count, rules)
        self.tapes_count = tapes_count
        self.rules = deepcopy(rules)
        self.init_state = init_state
        self.empty_symbol = empty_symbol

    def _assert_rules(self, tapes_count: int, rules: RulesType[ST, SYM]) -> None:
        for (_, symbols), (_, new_symbols, deltas) in rules.items():
            for x in [symbols, new_symbols, deltas]:
                if len(x) != tapes_count:
                    raise ValueError("Wrong number of tapes in rule!")

    def run(self,
            tapes: Sequence[list[SYM]],
            heads: Sequence[int] | None = None,
            max_steps: int | None = None
        ) -> list[list[SYM]]:
        """Run machine for given number of steps or until it halts. Returns tapes."""

        if len(tapes) != self.tapes_count:
            raise ValueError("Wrong number of input tapes, expected: {}, got: {}".format(self.tapes_count, len(tapes)))
        self.tapes = [tape.copy() for tape in tapes]

        if heads is None:
            heads = [0] * self.tapes_count
        if len(heads) != self.tapes_count:
            raise ValueError("Wrong number of heads, expected: {}, got: {}".format(self.tapes_count, len(heads)))
        self.heads = list(heads)

        self.halt = False
        self.state = self.init_state

        # maintain invariant: tape[head] is defined for all tapes
        for head, tape in zip(self.heads, self.tapes):
            if head < 0:
                raise ValueError("Head must be non-negative!")
            if head >= len(tape):
                tape.extend([self.empty_symbol] * (head - len(tape) + 1))

        step = 0
        while not self.halt:
            step += 1
            if (max_steps is not None) and (step > max_steps):
                break
            self._next()

        return self.tapes

    def _next(self) -> None:
        heads_data = tuple(tape[head] for head, tape in zip(self.heads, self.tapes))
        key = (self.state, heads_data)
        if key not in self.rules:
            self.halt = True
            return

        new_state, new_symbols, deltas = self.rules[key]
        for head, tape, new_symbol in zip(self.heads, self.tapes, new_symbols):
            tape[head] = new_symbol

        self.state = new_state
        self._move(deltas)

    def _move(self, deltas: tuple[DeltaType, ...]) -> None:
        for index, (head, tape, delta) in enumerate(zip(self.heads, self.tapes, deltas)):
            new_head = head + delta
            if new_head < 0:
                self.halt = True
                return
            if new_head == len(tape):
                tape.append(self.empty_symbol)
            self.heads[index] = new_head


#class MultitapeMachineWrapper[ST, SYM]:
#
#    type TapeType = list[SYM]
#
#    machine: TuringMachine[ST, SYM]
#
#    def __init__(self,
#            tapes_count: int,
#            multitape_rules: TODO,
#            empty_symbol: SYM,
#        ):
#        pass
#
#    def encode_tapes(self, tapes: list[TapeType]) -> TapeType:
#        pass
#
#    def decode_tape(self, tape: TapeType) -> list[TapeType]:
#        pass
