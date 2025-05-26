"""
This module implements almost classical Turing machine with rules:
    (state, symbol) -> (new_state, new_symbol, delta)
There are only two enchancements:
1) rule (state, None) -> _ allowed that applies for any current symbol
2) rule (state, _) -> (_, None, _) allowed that means that current symbol is not changed
"""

from copy import deepcopy
from collections.abc import Sequence, Hashable
from typing import Literal
import logging


type DeltaType = Literal[-1, 0, 1]


class TuringMachine[ST: Hashable, SYM: Hashable]:
    """
    Classical Turing machine.
    ST - States type
    SYM - Symbols type; None has special meaning and can't be a symbol.

    Rule: (state, symbol) -> (new_state, new_symbol, delta)
        delta = 0 is allowed
        symbol is None - means that the rule is applicable for any symbol
            (may be overriden by concrete rule)
        new_symbol is None - means that machine does not write
            (i.e. writes the same symbol as on the tape)
    """

    type RulesType[ST_, SYM_] = dict[tuple[ST_, SYM_ | None], tuple[ST_, SYM_ | None, DeltaType]]

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
            logging.debug('=======')
            logging.debug('step: %d', step)
            self._next()

        # maybe cleanup trailing empty symbols
        return self.tape

    def _next(self) -> None:
        key = (self.state, self.tape[self.head])
        logging.debug('state: %s | @[%d] => %s', key[0], self.head, key[1])
        logging.debug('tape: %s', self.tape)

        if key not in self.rules:
            logging.debug('key not found in rules: %s', key)
            key = (self.state, None)
            if key not in self.rules:
                logging.debug('halt: None key also not found')
                self.halt = True
                return

        new_state, new_symbol, delta = self.rules[key]
        logging.debug('rule -> %s | %s | %d', new_state, new_symbol, delta)

        if new_symbol is not None:
            self.tape[self.head] = new_symbol

        self.state = new_state
        if delta != 0:
            self._move(delta)

    def _move(self, delta: DeltaType) -> None:
        new_head = self.head + delta
        if new_head < 0:
            self.halt = True
            logging.debug('halt: out of tape')
            return
        if new_head == len(self.tape):
            self.tape.append(self.empty_symbol)
        self.head = new_head
