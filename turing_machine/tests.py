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
import universal


# TODO: add tests with symbols not in rules?


def test_repeat():
    machine = examples.get_repeat_machine()
    output = machine.run(tape=[], max_steps=9)
    expected = ['0', '_', '1', '_', '0', '_', '1', '_', '0']
    assert output[:-1] == expected  # TODO: strip empty symbols from the tape in TuringMachine?


def test_increment():
    machine = examples.get_increment_machine()
    output = machine.run(tape=['1', '0', '1'])
    expected = ['1', '1', '0']
    assert output[:-1] == expected


def test_copy1():
    machine = examples.get_copy1_machine()
    output = machine.run(tape=[1, 1, 1, 1])
    expected = [1, 1, 1, 1, 0, 1, 1, 1, 1]
    assert output == expected


def test_add():
    wrapper = examples.AddMachineWrapper()
    machine = wrapper.machine
    print('add machine:')
    print('  rules:', len(machine.rules))
    print('  states:', len(set(k[0] for k in machine.rules.keys())))

    for x in range(30):
        for y in range(30):
            output = machine.run(tape=wrapper.encode(x, y))
            result = wrapper.decode(output)
            assert result == x + y


def test_bin_inc():
    encoder = BinEncoder(examples.get_increment_machine())
    bin_machine = encoder.encode_machine()
    input = ['1', '0', '1']
    bin_tape = encoder.encode_input(input)
    bin_output = bin_machine.run(tape=bin_tape)
    output = encoder.decode_output(bin_output)
    expected = ['1', '1', '0']
    assert output[:-1] == expected


def test_bin_add():
    wrapper = examples.AddMachineWrapper()
    machine = wrapper.machine
    encoder = BinEncoder(machine)
    bin_machine = encoder.encode_machine()
    print('binarized add machine:')
    print('  block size:', encoder.block_size)
    print('  rules:', len(bin_machine.rules))
    print('  states:', len(set(k[0] for k in bin_machine.rules.keys())))

    cc = Counter()
    for (state, _), _ in bin_machine.rules.items():
        cc[state[0]] += 1
    print('  most common state groups:', cc.most_common(5))

    for x in range(15):
        for y in range(15):
            tape = wrapper.encode(x, y)
            bin_tape = encoder.encode_input(tape)
            bin_output = bin_machine.run(tape=bin_tape)
            output = encoder.decode_output(bin_output)
            result = wrapper.decode(output)
            assert result == x + y


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
    print('  rules:', len(machine.rules))
    print('  states:', len(set(k[0] for k in machine.rules.keys())))
    emulator = multitape.MultitapeEmulator(machine)

    print('  emulator rules:', len(emulator.machine.rules))
    print('  emulator states:', len(set(k[0] for k in emulator.machine.rules.keys())))

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


def test_universal():
    # basic test: multitape UTM on binary TM
    machine = examples.get_copy1_machine()
    N = 5
    input = [1] * N
    utm = universal.UniversalMachineWrapper()
    print('utm rules:', len(utm.machine.rules))
    utm_output = utm.machine.run(tapes=utm.encode(machine, input))
    output = utm.decode(utm_output)
    expected = [1] * N + [0] + [1] * N
    assert output == expected


def test_universal_on_binarized():
    # multitape UTM on simple binarized TM
    utm = universal.UniversalMachineWrapper()

    machine = examples.get_increment_machine()
    encoder = BinEncoder(machine)
    bin_machine = encoder.encode_machine()

    tape = ['1', '0', '1']
    bin_tape = encoder.encode_input(tape)

    utm_output = utm.machine.run(tapes=utm.encode(bin_machine, bin_tape))

    bin_output = utm.decode(utm_output)
    output = encoder.decode_output(bin_output)
    expected = ['1', '1', '0']
    assert output[:-1] == expected


def test_universal_add():
    # addition using multitape UTM
    utm = universal.UniversalMachineWrapper()

    wrapper = examples.AddMachineWrapper()
    machine = wrapper.machine
    encoder = BinEncoder(machine)
    bin_machine = encoder.encode_machine()

    x, y = 3, 5
    tape = wrapper.encode(x, y)
    bin_tape = encoder.encode_input(tape)
    utm_output = utm.machine.run(tapes=utm.encode(bin_machine, bin_tape))
    bin_output = utm.decode(utm_output)
    output = encoder.decode_output(bin_output)
    result = wrapper.decode(output)

    assert result == x + y


if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    test_repeat()
    test_increment()
    test_copy1()
    test_add()
    test_bin_add()
    test_bin_inc()
    test_multitape()
    test_multitape_emulator()
    test_universal()
    test_universal_on_binarized()
    test_universal_add()
    print('ok!')
