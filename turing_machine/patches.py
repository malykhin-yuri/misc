"""
We intentionaly keep TuringMachine main methods clean and simple.
Here are some patches that will help to shorten rules definition.
"""

from copy import deepcopy
from collections import defaultdict
from typing import Literal


type DeltaType = Literal[-1, 0, 1]
type RulesType[ST_, SYM_] = dict[tuple[ST_, SYM_], tuple[ST_, SYM_, DeltaType]]


def flatten_rules[ST, SYM](rules: dict[ST, dict[SYM, tuple[ST, SYM, DeltaType]]]) -> RulesType[ST, SYM]:
    """
    TuringMachine accepts rules (state, symbol) -> (new_state, new_symbol, delta).
    Often it is more convenient to create rules as: state -> (symbol -> ...)
    """
    result = {}
    for state, state_rules in rules.items():
        for symbol, new_data in state_rules.items():
            result[state, symbol] = new_data
    return result


def patch_rules[ST, SYM](rules: RulesType[ST, SYM]) -> RulesType[ST, SYM]:
    """
    Each rule maps: (curr_state, curr_symbol) -> (next_state, next_symbol, delta)
    Patches are applied in order:
    1) If curr_symbol is a frozenset of symbols, rules applies for each one
        (so symbols can't be fronzensets if you use this function)
    2) If there is only delta instead of triple, then next_state = next_symbol = None
    3) If new_state is None, then it becomes curr_state
    """
    rules = deepcopy(rules)

    fixed_rules = {}
    for (state, symbol), fixed_data in rules.items():
        if isinstance(symbol, frozenset):
            for s in symbol:
                fixed_rules[state, s] = fixed_data
        else:
            fixed_rules[state, symbol] = fixed_data
    rules = fixed_rules

    fixed_rules = {}
    for (state, symbol), new_data in rules.items():
        if isinstance(new_data, int):
            new_state, new_symbol, delta = None, None, new_data
        else:
            new_state, new_symbol, delta = new_data
        if new_state is None:
            new_state = state
        fixed_rules[state, symbol] = (new_state, new_symbol, delta)
    rules = fixed_rules

    return rules
