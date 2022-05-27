from synthbx.ast.clause import Clause


class Fact(Clause):
    def __init__(self, atom):
        self.atom = atom

    def __str__(self):
        return f'{self.atom}.'

    def __eq__(self, other):
        if isinstance(other, Fact):
            return self.__str__() == other.__str__()
        else:
            raise TypeError()

    def __lt__(self, other):
        if isinstance(other, Fact):
            return self.__str__() < other.__str__()
        else:
            raise TypeError()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())
