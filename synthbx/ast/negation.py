from synthbx.ast.literal import Literal
from synthbx.ast.atom import RejectAtom, ValidAtom


class Negation(Literal):
    def __init__(self, atom):
        self.atom = atom
        self.name = self.atom.name
        self.args = self.atom.args

    def __str__(self):
        return f'!{self.atom}'

    def __eq__(self, other):
        if isinstance(other, Literal):
            return self.__str__() == other.__str__()
        else:
            raise TypeError()

    def __lt__(self, other):
        if isinstance(other, Negation):
            return self.__str__() < other.__str__()
        else:
            raise TypeError()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())


class RejectNegation(Negation):
    def __init__(self):
        super().__init__(atom=RejectAtom())


class ValidNegation(Negation):
    def __init__(self):
        super().__init__(atom=ValidAtom())
