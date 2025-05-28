from collections import defaultdict
from collections.abc import Sequence
from enum import Enum
from typing import Any

from turing_machine import TuringMachine
import multitape


def get_repeat_machine():
    # This is the first example machine given by Alan Turing in his 1936 paper
    #   "On Computable Numbers, with an Application to
    #    the Entscheidungsproblem".
    # It simply writes the endless sequence 0 1 0 1 0 1...
    # From https://turingmachine.io
    rules = {
        ('b', '_'): ('c', '0', +1),
        ('c', '_'): ('e', None, +1),
        ('e', '_'): ('f', '1', +1),
        ('f', '_'): ('b', None, +1),
    }
    return TuringMachine(rules=rules, init_state='b', empty_symbol='_')


def get_increment_machine():
    rules = {
        ('right', '1'): ('right', None, +1),
        ('right', '0'): ('right', None, +1),
        ('right', '_'): ('carry', None, -1),
        ('carry', '1'): ('carry', '0', -1),
        ('carry', '0'): ('done', '1', -1),
    }
    return TuringMachine(rules=rules, init_state='right', empty_symbol='_')


def get_copy1_machine():
    # binary machine, see turingmachine.io
    rules = {
        ('each', 0): ('halt', None, +1),
        ('each', 1): ('sep', 0, +1),
        ('sep', 0): ('add', None, +1),
        ('sep', 1): ('sep', None, +1),
        ('add', 0): ('sepL', 1, -1),
        ('add', 1): ('add', None, +1),
        ('sepL', 0): ('next', None, -1),
        ('sepL', 1): ('sepL', None, -1),
        ('next', 0): ('each', 1, +1),
        ('next', 1): ('next', None, -1),
    }
    return TuringMachine(rules=rules, init_state='each', empty_symbol=0)


class AddMachineWrapper:
    # fast bin addition from turingmachine.io

    def __init__(self):
        self.machine = self._get_machine()

    @classmethod
    def encode(cls, x: int, y: int) -> list[str]:
        # we ensure x >= y to not get out of tape
        if x < y:
            return cls.encode(y, x)
        return ['_', '_'] + list(bin(x)[2:]) + ['+'] + list(bin(y)[2:])

    class States(Enum):
        INIT = 1
        RIGHT = 2
        READ = 3
        HAVE0 = 4
        HAVE1 = 5
        REWRITE = 6
        ADD0 = 7
        ADD1 = 8
        BACK0 = 9
        BACK1 = 10
        CARRY = 11
        DONE = 12
        def __repr__(self):
            return self._name_

    def _get_machine(self):
        S = self.States

        rules = {
            (S.INIT, '0'): (S.RIGHT, None, 0),
            (S.INIT, '1'): (S.RIGHT, None, 0),
            (S.INIT, None): (S.INIT, None, +1),

            # Start at the second number's rightmost digit.
            (S.RIGHT, '_'): (S.READ, None, -1),
            (S.RIGHT, None): (S.RIGHT, None, +1),

            # Add each digit from right to left:

            # read the current digit of the second number,
            (S.READ, '0'): (S.HAVE0, 'c', -1),
            (S.READ, '1'): (S.HAVE1, 'c', -1),
            (S.READ, '+'): (S.REWRITE, '_', -1),

            # and add it to the next place of the first number,
            # marking the place (using O or I) as already added.
            (S.HAVE0, '+'): (S.ADD0, None, -1),
            (S.HAVE0, None): (S.HAVE0, None, -1),
            (S.HAVE1, '+'): (S.ADD1, None, -1),
            (S.HAVE1, None): (S.HAVE1, None, -1),

            (S.ADD0, '0'): (S.BACK0, 'o', +1),
            (S.ADD0, '_'): (S.BACK0, 'o', +1),
            (S.ADD0, '1'): (S.BACK0, 'i', +1),
            (S.ADD0, 'o'): (S.ADD0, None, -1),
            (S.ADD0, 'i'): (S.ADD0, None, -1),

            (S.ADD1, '0'): (S.BACK1, 'i', +1),
            (S.ADD1, '_'): (S.BACK1, 'i', +1),
            (S.ADD1, '1'): (S.CARRY, 'o', -1),
            (S.ADD1, 'o'): (S.ADD1, None, -1),
            (S.ADD1, 'i'): (S.ADD1, None, -1),

            (S.CARRY, '0'): (S.BACK1, '1', +1),
            (S.CARRY, '_'): (S.BACK1, '1', +1),
            (S.CARRY, '1'): (S.CARRY, '0', -1),

            # Then, restore the current digit, and repeat with the next digit.
            (S.BACK0, 'c'): (S.READ, '0', -1),
            (S.BACK0, None): (S.BACK0, None, +1),
            (S.BACK1, 'c'): (S.READ, '1', -1),
            (S.BACK1, None): (S.BACK1, None, +1),

            # Finish: rewrite place markers back to 0s and 1s.
            (S.REWRITE, 'o'): (S.REWRITE, '0', -1),
            (S.REWRITE, 'i'): (S.REWRITE, '1', -1),
            (S.REWRITE, '0'): (S.REWRITE, None, -1),
            (S.REWRITE, '1'): (S.REWRITE, None, -1),
            (S.REWRITE, '_'): (S.DONE, None, 0),
        }

        return TuringMachine(rules=rules, init_state=S.INIT, empty_symbol='_')

    @staticmethod
    def decode(tape):
        # this is some cheating - cleanup should be made by TM itself
        # cleanup tape: _ sum _ y _
        while tape[-1] == '_':
            tape.pop()
        # remove y from tape
        while tape[-1] != '_':
            tape.pop()

        tape.pop()

        while tape[0] == '_':
            tape.pop(0)

        return int(''.join(tape), base=2)


def get_multitape_palyndrome_machine(base_alphabet: Sequence[str], start_symbol, empty_symbol='_'):
    rules: Any = {}
    rules['init'] = [
        ({0: start_symbol, 1: empty_symbol}, 'copy', {1: start_symbol}, {0: +1, 1: +1}),
    ]
    rules['copy'] = [
        ({0: empty_symbol, 1: empty_symbol}, 'left', {}, {0: -1}),
    ]
    for s in base_alphabet:
        rule = ({0: s, 1: empty_symbol}, 'copy', {1: s}, {0: +1, 1: +1})
        rules['copy'].append(rule)

    rules['left'] = [
        ({0: start_symbol, 1: empty_symbol}, 'test', {}, {0: +1, 1: -1}),
    ]
    for s in base_alphabet:
        rule = ({0: s, 1: empty_symbol}, 'left', {}, {0: -1})
        rules['left'].append(rule)

    rules['test'] = [
        ({0: empty_symbol, 1: start_symbol}, 'stop', {2: '1'}, {}),
    ]

    for s in base_alphabet:
        read = {0: s, 1: s}
        rule = (read, 'test', {}, {0: +1, 1: -1})
        rules['test'].append(rule)

    test_fail_rule = (None, 'stop', {2: '0'}, {})
    rules['test'].append(test_fail_rule)

    # we try to specify read data to reduce number of states
    for state_rules in rules.values():
        for read_data, _, _, _ in state_rules:
            if read_data is not None:
                read_data[2] = empty_symbol

    alphabet = [start_symbol, empty_symbol] + list(base_alphabet)
    final_rules = multitape.patch_partial(tapes_count=3, alphabet=alphabet, partial_rules=rules)

    return multitape.MultitapeTuringMachine(tapes_count=3, rules=final_rules, init_state='init', empty_symbol=empty_symbol)
