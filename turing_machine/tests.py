from collections import Counter
from typing import Any
import logging
import pprint
import string

from turing_machine import TuringMachine
import multitape
from patches import flatten_rules, patch_rules
import examples
from binarize import BinEncoder


# TODO: add tests with symbols not in rules?


def test_simple():
    machine = examples.get_simple_machine()
    output = machine.run(tape=[])
    encoder = BinEncoder(machine)
    bin_machine = encoder.encode_machine()
    bin_output = bin_machine.run(tape=[])
    assert encoder.decode_output(bin_output) == output


# TODO some wrapper for TuringMachine with prepare/parse tape methods?

def add_prepare_tape(x, y):
    return ['#'] + list(reversed(bin(x)[2:])) + ['+'] + list(reversed(bin(y)[2:])) + ['=']


def add_parse_tape(tape):
    bits = ''.join(reversed([x for x in tape if x in '01']))
    return int(bits, base=2)


def test_add():
    machine = examples.get_add_machine()
    for x in range(30):
        for y in range(30):
            output = machine.run(tape=add_prepare_tape(x, y))
            result = add_parse_tape(output)
            assert(result == x + y)


def test_bin_add():
    encoder = BinEncoder(examples.get_add_machine())
    bin_machine = encoder.encode_machine()

    for x in range(15):
        for y in range(15):
            tape = add_prepare_tape(x, y)
            bin_tape = encoder.encode_input(tape)
            bin_output = bin_machine.run(tape=bin_tape)
            output = encoder.decode_output(bin_output)
            result = add_parse_tape(output)
            assert(result == x + y)


def test_multitape():
    machine = examples.get_multitape_palyndrome_machine(base_alphabet=list(string.ascii_letters), start_symbol='>')
    expected = [('abba', True), ('abbc', False), ('', True), ('dadda', False), ('daddad', True), ('VV', True)]
    for data, is_palyndrome in expected:
        tape = ['>'] + list(data)
        output_tapes = machine.run(tapes=[tape, [], []])
        result = bool(int(output_tapes[-1][0]))
        assert is_palyndrome == result, "failed on data: {}".format(data)


def test_multitape_emulator():
    print('palindrome machine (multitape emulator)')
    machine = examples.get_multitape_palyndrome_machine(base_alphabet=list('abcdefghijk'), start_symbol='*')
    print('rules:', len(machine.rules))
    print('states:', len(set(k[0] for k in machine.rules.keys())))
    emulator = multitape.MultitapeEmulator(machine)

    print('emulator rules:', len(emulator.machine.rules))
    print('emulator states:', len(set(k[0] for k in emulator.machine.rules.keys())))

    cc = Counter()
    for (state, _), _ in emulator.machine.rules.items():
        cc[state[0]] += 1
    print(cc.most_common(5))

    expected = [('abba', True), ('abbc', False), ('', True), ('dadda', False), ('daddad', True)]
    for data, is_palyndrome in expected:
        input_tape = ['*'] + list(data)
        tapes=[input_tape, [], []]
        tm_tape = emulator.encode_tapes(tapes)
        tm_output = emulator.machine.run(tape=tm_tape)
        output_tapes = emulator.decode_tape(tm_output)
        result = bool(int(output_tapes[-1][0]))
        assert is_palyndrome == result


if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    test_simple()
    test_add()
    test_bin_add()
    test_multitape()
    test_multitape_emulator()
