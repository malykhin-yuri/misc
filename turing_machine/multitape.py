"""
Multitape Turing Machine.
This module also will provide wrapper to emulate MTM by a regular TM
"""

from collections import Counter
from collections.abc import Sequence, Iterable
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Literal, Any
import logging
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
            write_full_data = tuple(write_data.get(index) for index in range(tapes_count))
            full_deltas = tuple(deltas.get(index, 0) for index in range(tapes_count))
            if read_data is None:
                result[state, None] = (new_state, write_full_data, full_deltas)
                continue

            # read_data is partial dict, fill in gaps
            for missing_tuple in itertools.product(alphabet_list, repeat=tapes_count - len(read_data)):
                missing = list(missing_tuple)
                read_full_data: list[SYM] = []
                for index in range(tapes_count):
                    if index in read_data:
                        read_full_data.append(read_data[index])
                    else:
                        read_full_data.append(missing.pop(0))
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
                if x is not None and len(x) != tapes_count:
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
            key = (self.state, None)
            if key not in self.rules:
                self.halt = True
                return

        new_state, new_symbols, deltas = self.rules[key]
        for head, tape, new_symbol in zip(self.heads, self.tapes, new_symbols):
            if new_symbol is not None:
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


class EmulatorStateGroup(IntEnum):
    REGULAR = 10
    READ = 20
    READ_ANY = 21
    WRITE = 30
    MOVE_INIT = 40
    MOVE_DO = 41
    MOVE_DONE = 42
    def __repr__(self):
        return self._name_


type RichSt[ST_] = tuple[EmulatorStateGroup, ST_, int, Any]  # int - tape_index

@dataclass(frozen=True)
class RichSym[SYM_]:
    symbol: SYM_
    flag: bool
    def __repr__(self):
        fmt = '<{0}>' if self.flag else '{0}'
        return fmt.format(self.symbol)


class MultitapeEmulator[ST, SYM]:
    """
    Emulate MTM using regular TM. Does not support heads argument in run(), (TODO!) assume starting with 0.

    TODO: about implementation (tape k of T => real tape [index * T + k]; RichSym(s, True) means that multihead is there.
    """

    machine: TuringMachine[RichSt[ST], RichSym[SYM]]

    def __init__(self, multitape_machine: MultitapeTuringMachine[ST, SYM]) -> None:
        self.machine = self._get_machine(multitape_machine)
        self.tapes_count = multitape_machine.tapes_count
        self.orig_empty_symbol = multitape_machine.empty_symbol

    def _get_machine(self, multitape_machine: MultitapeTuringMachine[ST, SYM]) -> TuringMachine[RichSt[ST], RichSym[SYM]]:
        T = multitape_machine.tapes_count
        G = EmulatorStateGroup
        RS = RichSym
        init_state = (G.REGULAR, multitape_machine.init_state, 0, None)
        empty_symbol = RS(multitape_machine.empty_symbol, False)

        alphabet = {multitape_machine.empty_symbol}
        for (orig_state, orig_symbols), (new_orig_state, new_orig_symbols, deltas) in multitape_machine.rules.items():
            if orig_symbols is not None:
                alphabet.update(s for s in orig_symbols if s is not None)
            alphabet.update(s for s in new_orig_symbols if s is not None)

        rules: dict[tuple[RichSt[ST], RichSym[SYM]], tuple[RishSt[ST], RichSym[SYM], DeltaType]] = {}  # type: ignore

        def switch_internal_state(state1: RichSt[ST], state2: RichSt[ST], delta: DeltaType = 0) -> None:
            rules[state1, None] = (state2, None, delta)

        seen_move_states = set()

        has_default_rule = set()
        has_regular_rule = set()
        for (orig_state, orig_symbols), _ in multitape_machine.rules.items():
            if orig_symbols is None:
                has_default_rule.add(orig_state)
            else:
                has_regular_rule.add(orig_state)

        for (orig_state, orig_symbols), (new_orig_state, new_orig_symbols, deltas) in multitape_machine.rules.items():
            for tape_index in range(T):
                # invariant: in regular state all multiheads are to the right of real head
                regular_state = (G.REGULAR, orig_state, tape_index, None)

                read_common_finish_state: RichSt[ST]

                if orig_symbols is None:
                    if orig_state not in has_regular_rule:
                        readany_start_state = (G.READ_ANY, orig_state, tape_index, 0)
                        switch_internal_state(regular_state, readany_start_state)
                    # ^^^ otherwise we will get to READ_ANY only from READ states
                    for count in range(T):
                        readany_curr_state = (G.READ_ANY, orig_state, tape_index, count)
                        next_tape_index = (tape_index + 1) % T
                        for s in alphabet:
                            readany_more_state = (G.READ_ANY, orig_state, next_tape_index, count + 1)
                            rules[readany_curr_state, RS(s, True)] = (readany_more_state, RS(s, True), +1)
                        readany_next_state = (G.READ_ANY, orig_state, next_tape_index, count)
                        rules[readany_curr_state, None] = (readany_next_state, None, +1)
                    readany_finish_state = (G.READ_ANY, orig_state, tape_index, T)
                    read_common_finish_state = readany_finish_state
                else:
                    read_data: tuple[SYM | None, ...] = (None,) * T
                    read_start_state = (G.READ, orig_state, tape_index, read_data)
                    switch_internal_state(regular_state, read_start_state)

                    next_tape_index = (tape_index + 1) % T
                    prev_tape_index = (tape_index - 1) % T
                    for read_mask in itertools.product([True, False], repeat=T):
                        if sum(read_mask) == T:
                            continue  # everything was read, see later
                        read_data = tuple(orig_symbols[index] if read_mask[index] else None for index in range(T))
                        read_curr_state = (G.READ, orig_state, tape_index, read_data)

                        expected_orig_symbol = orig_symbols[tape_index]
                        head_symbol = RS(expected_orig_symbol, True)
                        new_read_data = read_data[:tape_index] + (expected_orig_symbol,) + read_data[(tape_index + 1):]
                        read_new_symbol_state = (G.READ, orig_state, next_tape_index, new_read_data)
                        rules[read_curr_state, head_symbol] = (read_new_symbol_state, head_symbol, +1)  # read!
                        for s in alphabet:
                            read_next_state = (G.READ, orig_state, next_tape_index, read_data)
                            rules[read_curr_state, RS(s, False)] = (read_next_state, RS(s, False), +1)  # TODO write None

                        # fallback to None symbol rule (if exists)
                        if orig_state in has_default_rule:
                            read_count = sum(1 for x in read_data if x is not None)
                            readany_state = (G.READ_ANY, orig_state, next_tape_index, read_count + 1)
                            rules[read_curr_state, None] = (readany_state, None, +1)

                    read_finish_state = (G.READ, orig_state, tape_index, orig_symbols)
                    read_common_finish_state = read_finish_state

                # change state and start to write/move heads
                write_start_storage = (tuple((s, 2) for s in new_orig_symbols), deltas)  # 2: must write; 1: must seen; 0: done
                write_start_state = (G.WRITE, new_orig_state, tape_index, write_start_storage)
                switch_internal_state(read_common_finish_state, write_start_state)

                for written_values in itertools.product([0, 1, 2], repeat=T):
                    remain_count = sum(x > 0 for x in written_values)
                    if remain_count == 0:
                        continue

                    to_write = tuple((s, v) for s, v in zip(new_orig_symbols, written_values))
                    write_storage = (to_write, deltas)
                    write_curr_state = (G.WRITE, new_orig_state, tape_index, write_storage)

                    if written_values[tape_index] == 2:
                        for orig_symbol in alphabet:
                            head_symbol = RS(orig_symbol, True)
                            if deltas[tape_index] == -1:
                                new_value = 1  # should see new head to regular state work properly (all heads to the right)
                            else:
                                new_value = 0  # all done here
                            new_to_write = list(to_write)
                            new_to_write[tape_index] = (to_write[tape_index][0], new_value)
                            if remain_count == 1 and new_value == 0:
                                dw = 0
                            else:
                                dw = -1
                            new_tape_index = (tape_index + dw) % T
                            write_next_state = (G.WRITE, new_orig_state, new_tape_index, (tuple(new_to_write), deltas))
                            write_symbol = new_orig_symbols[tape_index]
                            write_rich_symbol = RS(write_symbol, True) if write_symbol is not None else None
                            if deltas[tape_index] != 0:
                                move_start_state = (G.MOVE_INIT, new_orig_state, tape_index, (write_storage, deltas[tape_index]))
                                rules[write_curr_state, head_symbol] = (move_start_state, write_rich_symbol, 0)  # write!
                                seen_move_states.add(move_start_state)
                                move_finish_state = (G.MOVE_DONE, new_orig_state, tape_index, write_storage)
                                switch_internal_state(move_finish_state, write_next_state, dw)
                            else:
                                rules[write_curr_state, head_symbol] = (write_next_state, write_rich_symbol, dw)  # write!
                    elif written_values[tape_index] == 1:
                        for s in alphabet:
                            head_symbol = RS(s, True)
                            if remain_count == 1:
                                dw = 0
                            else:
                                dw = -1
                            new_to_write = list(to_write)
                            new_to_write[tape_index] = (to_write[tape_index][0], 0)
                            new_storage = (tuple(new_to_write), deltas)
                            write_next_state = (G.WRITE, new_orig_state, (tape_index + dw) % T, new_storage)
                            rules[write_curr_state, head_symbol] = (write_next_state, head_symbol, dw)

                    for s in alphabet:
                        rules[write_curr_state, RS(s, False)] = (
                            (G.WRITE, new_orig_state, (tape_index - 1) % T, write_storage),
                            RS(s, False),
                            -1,
                        )

                write_last_state = (G.WRITE, new_orig_state, tape_index, (tuple((s, 0) for s in new_orig_symbols), deltas))
                regular_next_state = (G.REGULAR, new_orig_state, tape_index, None)
                switch_internal_state(write_last_state, regular_next_state)

        # move (nonzero deltas - this reduces states size)
        for move_start_state in seen_move_states:
            # we do not change tape_index in MOVE
            _, orig_state, tape_index, (write_storage, delta) = move_start_state
            for s in alphabet:
                to_move = delta * T
                to_return = -delta * T

                move_start_go = (G.MOVE_DO, orig_state, tape_index, (write_storage, to_move, to_return, False))
                rules[move_start_state, RS(s, True)] = (move_start_go, RS(s, False), 0)

                for m in range(T):
                    move_curr_state = (G.MOVE_DO, orig_state, tape_index, (write_storage, (m+1) * delta, to_return, False))
                    move_next_state = (G.MOVE_DO, orig_state, tape_index, (write_storage, m*delta, to_return, False))
                    for flag in [True, False]:
                        rules[move_curr_state, RS(s, flag)] = (move_next_state, RS(s, flag), delta)

                move_intermediate_state = (G.MOVE_DO, orig_state, tape_index, (write_storage, 0, to_return, False))
                move_start_return_state = (G.MOVE_DO, orig_state, tape_index, (write_storage, 0, to_return, True))
                rules[move_intermediate_state, RS(s, False)] = (move_start_return_state, RS(s, True), 0)

                for m in range(T):
                    move_curr_state = (G.MOVE_DO, orig_state, tape_index, (write_storage, 0, -(m+1) * delta, True))
                    move_next_state = (G.MOVE_DO, orig_state, tape_index, (write_storage, 0, -m * delta, True))
                    for flag in [True, False]:
                        rules[move_curr_state, RS(s, flag)] = (move_next_state, RS(s, flag), -delta)

            move_last_state = (G.MOVE_DO, orig_state, tape_index, (write_storage, 0, 0, True))
            move_finish_state = (G.MOVE_DONE, orig_state, tape_index, write_storage)
            switch_internal_state(move_last_state, move_finish_state)

        return TuringMachine(rules=rules, init_state=init_state, empty_symbol=empty_symbol)

    def encode_tapes(self, tapes: Sequence[list[SYM]]) -> list[RichSym[SYM]]:
        """Converts to one tape and sets heads = 0."""
        if len(tapes) != self.tapes_count:
            raise ValueError("Wrong number of tapes, expected: {}, got: {}".format(self.tapes_count, len(tapes)))

        # we have to add empty symbols manually to ensure markers
        tapes_list = [tape.copy() for tape in tapes]
        for tape in tapes_list:
            if len(tape) == 0:
                tape.append(self.orig_empty_symbol)

        result_tape = []
        max_len = max(len(tape) for tape in tapes)
        for symbol_index in range(max_len):
            is_head = (symbol_index == 0)
            for tape_index in range(self.tapes_count):
                tape = tapes_list[tape_index]
                orig_symbol = tape[symbol_index] if symbol_index < len(tape) else self.orig_empty_symbol
                result_tape.append(RichSym(orig_symbol, is_head))

        return result_tape

    def decode_tape(self, tape: list[RichSym[SYM]]) -> list[list[SYM]]:
        tapes: list[list[SYM]] = [[] for _ in range(self.tapes_count)]
        for index, symbol in enumerate(tape):
            tapes[(index % self.tapes_count)].append(symbol.symbol)
        return tapes
