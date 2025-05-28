from enum import Enum
import itertools
import logging
from typing import Literal

from multitape import MultitapeTuringMachine
from turing_machine import TuringMachine


type Bits = Literal[0, 1]
STR_BITS = ['0', '1']


class States(Enum):
    # top-level functions

    MAIN_INIT = 10
    MAIN_LOOKUP = 11
    MAIN_APPLY = 12
    MAIN_RETURN = 13

    LOOKUP_SEARCH = 20
    LOOKUP_CHECK = 21
    LOOKUP_FOUND_STATE = 22

    APPLY_WRITE = 30
    APPLY_MOVE = 31
    APPLY_CHANGE_STATE = 32

    RETURN_0 = 40
    RETURN_1 = 41

    HALT = 50  # technically, this is just a regular state, but with no rules so TM halts immediately

    # auxiliary functions

    FIND_NEXT = 70

    COMPARE_GO_LEFT = 80
    COMPARE_CHECK = 81

    MOVE = 90

    CHANGE_STATE_GO_RIGHT = 100
    CHANGE_STATE_ERASE = 101
    CHANGE_STATE_COPY = 102

    def __repr__(self):
        return self._name_


type Alphabet = Literal[
    '_',                # empty symbol
    '0', '1',           # bits - used for input bits and binary encoding of states and delta
    '-',                # used for None symbol and for delta = -1
    '>',                # start of each tape
    '/',                # delimiter
    '#',                # end of rules
]


class UniversalMachineWrapper:
    machine: MultitapeTuringMachine[States, Alphabet]

    # UTM is multitape machine with 3 tapes:
    # [0] - TM rules code;
    # [1] - work where we store current TM state (binary code)
    # [2] - work where we emulate TM tape (starts with TM input)
    # The constants 0,1,2 are hard-coded in code

    def __init__(self):
        self._alphabet_list = ['_', '0', '1', '-', '>', '/', '#']
        self._rules = {}  # used in self._switch
        self._build_machine()  # build self.machine

    @classmethod
    def encode[ST](cls, machine: TuringMachine[ST, Bits], tape: list[Bits]) -> list[list[Alphabet]]:
        return [
            ['>'] + cls._encode_tm(machine),
            ['>'] + ['0'],  # TM init state
            ['>'] + cls._encode_input(tape),
        ]

    @staticmethod
    def _encode_tm[ST](machine: TuringMachine[ST, Bits]) -> list[Alphabet]:
        assert machine.empty_symbol == 0  # common convention, supported in binarizer

        # state _ symbol new_symbol delta new_state _ / .... / ... #
        # 1 0 1 _ 1      0          -     1 1 0 0   _ / .... / ... #
        state_index = {machine.init_state: 0}
        logging.debug('state[0] (init): %s', machine.init_state)
        for (state, _), (new_state, _, _) in machine.rules.items():
            for st in [state, new_state]:
                if st not in state_index:
                    new_index = len(state_index)
                    state_index[st] = new_index
                    logging.debug('state[%d]: %s => %s', new_index, st, bin(new_index)[2:])
        data = []

        # in order to lookup work correctly we first write regular rules
        regular_rules = []
        fallback_rules = []

        for (state, bit), (new_state, new_bit, delta) in machine.rules.items():
            rule = (state, bit, new_state, new_bit, delta)
            if bit is None:
                fallback_rules.append(rule)
            else:
                regular_rules.append(rule)

        tape = []
        rules_count = len(regular_rules) + len(fallback_rules)
        for rule_index, (state, bit, new_state, new_bit, delta) in enumerate(regular_rules + fallback_rules):
            state_binary = bin(state_index[state])[2:]
            tape.extend(state_binary)
            tape.append('_')
            tape.append(str(bit) if bit is not None else '-')

            tape.append(str(new_bit) if new_bit is not None else '-')
            tape.append(str(delta) if delta >= 0 else '-')
            new_state_binary = bin(state_index[new_state])[2:]
            tape.extend(new_state_binary)
            tape.append('_')

            delimiter = '#' if rule_index == rules_count - 1 else '/'
            tape.append(delimiter)

        return tape

    @staticmethod
    def _encode_input(tape: list[Bits]) -> list[Alphabet]:
        return [str(bit) for bit in tape]

    def _switch(self, state, new_state, symbol=None, new_symbol=(None, None, None), delta=(0, 0, 0)):
        if symbol is None:
            self._rules[state, symbol] = (new_state, new_symbol, delta)
            return

        symbol_variants = []
        for tape_index, s in enumerate(symbol):
            if s is not None:
                symbol_variants.append([s])
            elif tape_index == 0:
                symbol_variants.append(self._alphabet_list)
            else:
                symbol_variants.append(['>', '0', '1', '_'])

        for symbol_full in itertools.product(*symbol_variants):
            self._rules[state, symbol_full] = (new_state, new_symbol, delta)

    def _build_machine(self):
        # Here we use the following style: some action (e.g., lookup) is implemented
        # as a python function with args: enter state, exit state (one or more, if there are
        # various outcomes). Inside we introduce a group of states and set up rules between them.
        # Current function describes high-level logic.

        S = States
        self._switch(S.MAIN_INIT, S.MAIN_LOOKUP, delta=(+1, +1, +1))

        # cycle; invariant: MAIN_LOOKUP heads[0] = 1, heads[2] emulates TM head
        self._do_lookup(enter=S.MAIN_LOOKUP, exit_found=S.MAIN_APPLY, exit_not_found=S.HALT)
        self._do_apply(enter=S.MAIN_APPLY, exit=S.MAIN_RETURN, exit_out_of_tape=S.HALT)
        self._do_return(enter=S.MAIN_RETURN, exit=S.MAIN_LOOKUP)

        self.machine = MultitapeTuringMachine(tapes_count=3, rules=self._rules, init_state=S.MAIN_INIT, empty_symbol='_')

    def _do_lookup(self, enter, exit_found, exit_not_found):
        # pre: heads[0] = 1
        # post: heads[0] is on the start of the rule value (new_symbol; see _encode_tm)
        S = States
        self._switch(enter, S.LOOKUP_CHECK)  # first time already at the start
        self._do_find_next_rule(S.LOOKUP_SEARCH, exit_found=S.LOOKUP_CHECK, exit_not_found=exit_not_found)
        self._do_compare_states(S.LOOKUP_CHECK, exit_equal=S.LOOKUP_FOUND_STATE, exit_not_equal=S.LOOKUP_SEARCH)
        self._do_compare_symbols(S.LOOKUP_FOUND_STATE, exit_equal=exit_found, exit_not_equal=S.LOOKUP_SEARCH)

    def _do_find_next_rule(self, enter, exit_found, exit_not_found):
        state = States.FIND_NEXT
        self._switch(enter, state)
        self._switch(state, exit_not_found, symbol=('#', None, None))
        self._switch(state, exit_found, symbol=('/', None, None), delta=(+1, 0, 0))
        self._switch(state, state, delta=(+1, 0, 0))

    def _do_compare_states(self, enter, exit_equal, exit_not_equal):
        # pre: heads[0] on the start of state
        # post: heads[0] after "_" state delimiter
        S = States
        self._switch(enter, S.COMPARE_GO_LEFT)  # move heads[1] to start (index=1)
        self._switch(S.COMPARE_GO_LEFT, S.COMPARE_CHECK, symbol=(None, '>', None), delta=(0, +1, 0))
        self._switch(S.COMPARE_GO_LEFT, S.COMPARE_GO_LEFT, delta=(0, -1, 0))

        for str_bit in STR_BITS:
            self._switch(S.COMPARE_CHECK, S.COMPARE_CHECK, symbol=(str_bit, str_bit, None), delta=(+1, +1, 0))
        self._switch(S.COMPARE_CHECK, exit_equal, symbol=('_', '_', None), delta=(+1, 0, 0))
        self._switch(S.COMPARE_CHECK, exit_not_equal)

    def _do_compare_symbols(self, enter, exit_equal, exit_not_equal):
        # pre: head[0] is on the symbol of the rule
        # post: head is moved ahead
        for str_bit in STR_BITS:
            self._switch(enter, exit_equal, symbol=(str_bit, None, str_bit), delta=(+1, 0, 0))
        self._switch(enter, exit_equal, symbol=('-', None, None), delta=(+1, 0, 0))
        self._switch(enter, exit_not_equal)

    def _do_apply(self, enter, exit, exit_out_of_tape):
        # pre: head[0] is on the new symbol
        S = States
        self._switch(enter, S.APPLY_WRITE)
        self._do_write(enter=S.APPLY_WRITE, exit=S.APPLY_MOVE)
        self._do_move(enter=S.APPLY_MOVE, exit=S.APPLY_CHANGE_STATE, exit_out_of_tape=exit_out_of_tape)
        self._do_change_state(enter=S.APPLY_CHANGE_STATE, exit=exit)

    def _do_write(self, enter, exit):
        # pre: heads[0] is on the new symbol
        # post: head is moved ahead
        for str_bit in STR_BITS:
            self._switch(enter, exit, symbol=(str_bit, None, None), new_symbol=(None, None, str_bit), delta=(+1, 0, 0))
        self._switch(enter, exit, symbol=('-', None, None), delta=(+1, 0, 0))

    def _do_move(self, enter, exit, exit_out_of_tape):
        # pre: head[0] is on the delta
        # post: head is moved ahead
        S = States
        self._switch(enter, S.MOVE, symbol=('1', None, None), delta=(+1, 0, +1))
        self._switch(enter, S.MOVE, symbol=('-', None, None), delta=(+1, 0, -1))
        self._switch(enter, S.MOVE, symbol=('0', None, None), delta=(+1, 0, 0))
        self._switch(S.MOVE, exit, symbol=(None, None, '_'), new_symbol=(None, None, '0'))  # TM empty symbol
        self._switch(S.MOVE, exit_out_of_tape, symbol=(None, None, '>'))
        self._switch(S.MOVE, exit)

    def _do_change_state(self, enter, exit):
        # pre: heads[0] = start of new_state
        S = States
        self._switch(enter, S.CHANGE_STATE_GO_RIGHT)
        self._switch(S.CHANGE_STATE_GO_RIGHT, S.CHANGE_STATE_ERASE, symbol=(None, '_', None), delta=(0, -1, 0))
        self._switch(S.CHANGE_STATE_GO_RIGHT, S.CHANGE_STATE_GO_RIGHT, delta=(0, +1, 0))

        self._switch(S.CHANGE_STATE_ERASE, S.CHANGE_STATE_COPY, symbol=(None, '>', None), delta=(0, +1, 0))
        self._switch(S.CHANGE_STATE_ERASE, S.CHANGE_STATE_ERASE, new_symbol=(None, '_', None), delta=(0, -1, 0))

        self._switch(S.CHANGE_STATE_COPY, exit, symbol=('_', None, None))
        for str_bit in STR_BITS:
            self._switch(
                S.CHANGE_STATE_COPY,
                S.CHANGE_STATE_COPY,
                symbol=(str_bit, None, None),
                new_symbol=(None, str_bit, None),
                delta=(+1, +1, 0),
            )

    def _do_return(self, enter, exit):
        # returns heads of tapes [0], [1] to index=1
        S = States

        # first we move head[0]
        self._switch(enter, S.RETURN_0)
        self._switch(S.RETURN_0, S.RETURN_1, symbol=('>', None, None))
        self._switch(S.RETURN_0, S.RETURN_0, delta=(-1, 0, 0))

        self._switch(S.RETURN_1, exit, symbol=('>', '>', None), delta=(+1, +1, 0))
        self._switch(S.RETURN_1, S.RETURN_1, delta=(0, -1, 0))

    @staticmethod
    def decode(tapes: list[list[Alphabet]]) -> list[Bits]:
        output = tapes[2].copy()
        output.pop(0)  # remove '>'
        if len(output) > 0 and output[-1] == '_':
            # only one trailing UTM empty symbol may occur
            output.pop()
        return [int(x) for x in output]
