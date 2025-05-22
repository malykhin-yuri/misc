from collections import defaultdict

from turing_machine import TuringMachine
from patches import flatten_rules, patch_rules


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
