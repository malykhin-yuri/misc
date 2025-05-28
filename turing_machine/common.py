class PrettyTape:
    def __init__(self, tape, head=0):
        self.tape = tape
        self.head = head
    def __repr__(self):
        reprs = []
        for index, item in enumerate(self.tape):
            if index == self.head:
                item_repr = '[{}]'.format(item)
            else:
                item_repr = '{:^3}'.format(str(item))
            reprs.append(item_repr)
        return '@{}: |'.format(self.head) + '|'.join(reprs) + '|'

