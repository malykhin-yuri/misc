from typing import Any
import logging

from turing_machine import TuringMachine
from patches import flatten_rules, patch_rules
from examples import get_add_machine
from binarize import BinEncoder


# TODO some wrapper for TuringMachine with prepare/parse tape methods?

def add_prepare_tape(x, y):
    return ['#'] + list(reversed(bin(x)[2:])) + ['+'] + list(reversed(bin(y)[2:])) + ['=']


def add_parse_tape(tape):
    bits = ''.join(reversed([x for x in tape if x in '01']))
    return int(bits, base=2)


def test_add():
    machine = get_add_machine()
    for x in range(5):
        for y in range(5):
            output = machine.run(tape=add_prepare_tape(x, y))
            result = add_parse_tape(output)
            assert(result == x + y)


def test_bin_add():
    machine = get_add_machine()
    encoder = BinEncoder(machine)
    bin_machine = encoder.encode_machine()

    for x in range(5):
        for y in range(5):
            tape = add_prepare_tape(x, y)
            bin_tape = encoder.encode_input(tape)

            bin_output = bin_machine.run(tape=bin_tape)
            output = encoder.decode_output(bin_output)

            result = add_parse_tape(output)
            assert(result == x + y)


if __name__ == "__main__":
    test_add()
    test_add()
    test_bin_add()
