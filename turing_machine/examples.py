from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from turing_machine import TuringMachine
import multitape
from patches import flatten_rules, patch_rules


def get_simple_machine():
    INIT = 'INIT'
    WORK = 'WORK'
    rules = {
        INIT: {
            '_': (WORK, 'a', +1),
        },
        WORK: {
            'a': (WORK, 'b', +1),
            '_': (WORK, 'a', -1),
        },
    }
    return TuringMachine(rules=flatten_rules(rules), init_state=INIT, empty_symbol='_')


def get_add_machine():
    type State = str
    rules = defaultdict(dict)
    INIT = ('LEFT', 0)  # 0 = carry bit
    for carry in [0, 1]:
        # move head left to 0
        move_left: State = ('LEFT', carry)
        read_start: State = ('READ', carry, None, None)
        rules[move_left] = {
            frozenset({'0', '1', '+', '_', '='}): -1,
            '#': [read_start, '#', 0],
        }

        # read last digits, store them in state
        rules[read_start] = {
            frozenset({'#', '_'}): +1,
            '0': [('READ', carry, '0', None), '_', +1],
            '1': [('READ', carry, '1', None), '_', +1],
            '+': [('READ2', carry, '.', None), None, +1],  # first number is exhausted
        }
        for bit in ['0', '1', '.']:
            state = ('READ', carry, bit, None)
            rules[state] = {
                frozenset({'0', '1', '_'}): +1,
                '+': [('READ2', carry, bit, None), '+', +1],
            }

        for bit in ['0', '1', '.']:
            state = ('READ2', carry, bit, None)
            rules[state] = {
                '_': +1,
                '0': [('READ2', carry, bit, '0'), '_', +1],
                '1': [('READ2', carry, bit, '1'), '_', +1],
                '=': [('WRITE', carry, bit, '.'), None, +1],  # second number is exhausted
            }

        # write
        for bit1 in ['0', '1', '.']:
            for bit2 in ['0', '1', '.']:
                state = ('READ2', carry, bit1, bit2)
                wrstate = ('WRITE', carry, bit1, bit2)
                rules[state] = {
                    '0': +1,
                    '1': +1,
                    '=': [wrstate, None, +1],
                }
                bit1_value = 1 if bit1 == '1' else 0
                bit2_value = 1 if bit2 == '1' else 0
                bitsum = bit1_value + bit2_value + carry
                if bitsum >= 2:
                    wr_bit = bitsum - 2
                    new_carry = 1
                else:
                    wr_bit = bitsum
                    new_carry = 0

                rules[wrstate] = {
                    '0': +1,
                    '1': +1,
                }
                if bit1 == '.' and bit2 == '.':
                    rules[wrstate]['_'] = ['STOP', str(wr_bit), 0]
                else:
                    rules[wrstate]['_'] = [('LEFT', new_carry), str(wr_bit), 0]

    final_rules = patch_rules(flatten_rules(rules))
    return TuringMachine(rules=final_rules, init_state=INIT, empty_symbol='_')


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
