from copy import deepcopy
from collections.abc import Sequence
from typing import Literal
import logging


type DeltaType = Literal[-1, 0, 1]


class TuringMachine[ST, SYM]:
    type RulesType[ST_, SYM_] = dict[tuple[ST_, SYM_], tuple[ST_, SYM_, DeltaType]]

    def __init__(self,
            rules: RulesType[ST, SYM],  # machine halts iff rules are not defined
            init_state: ST,
            empty_symbol: SYM,
        ):
        self.rules = deepcopy(rules)
        self.init_state = init_state
        self.empty_symbol = empty_symbol

    def run(self,
            tape: list[SYM],  # initial symbols on the tape
            head: int = 0,
            max_steps: int | None = None
        ) -> list[SYM]:
        """Run machine for given number of steps or until it halts. Returns tape."""

        self.halt = False
        self.state = self.init_state
        self.tape = tape.copy()
        # maintain invariant: tape[head] is defined
        if head < 0:
            raise ValueError("Head must be non-negative!")
        if head >= len(tape):
            self.tape.extend([self.empty_symbol] * (head - len(tape) + 1))
        self.head = head

        step = 0
        while not self.halt:
            step += 1
            if (max_steps is not None) and (step > max_steps):
                break
            self._next()

        # maybe cleanup trailing empty symbols
        return self.tape

    def _next(self) -> None:
        logging.debug('state: %s, tape: %s, head: %s', self.state, self.tape, self.head)
        key = (self.state, self.tape[self.head])
        if key not in self.rules:
            self.halt = True
            return

        new_state, new_symbol, delta = self.rules[key]
        self.tape[self.head] = new_symbol
        self.state = new_state
        self._move(delta)

    def _move(self, delta: DeltaType) -> None:
        new_head = self.head + delta
        if new_head < 0:
            self.halt = True
            return
        if new_head == len(self.tape):
            self.tape.append(self.empty_symbol)
        self.head = new_head
