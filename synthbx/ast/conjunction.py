from synthbx.ast.unit import Unit
from synthbx.ast.atom import Atom
from synthbx.ast.negation import Negation
from synthbx.ast.constraint import Constraint


class Conjunction(Unit):
    def __init__(self, items):
        self.items = items

    def __str__(self):
        return ', '.join([str(i) for i in self.items])

    def __eq__(self, other):
        if isinstance(other, Conjunction):
            return self.__str__() == other.__str__()
        else:
            TypeError()

    def __lt__(self, other):
        if isinstance(other, Conjunction):
            return self.__str__() < other.__str__()
        else:
            TypeError()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    def partition(self):
        pl_list = [l for l in self.items if type(l) is Atom]
        nl_list = [l for l in self.items if type(l) is Negation]
        cs_list = [l for l in self.items if type(l) is Constraint]
        return (pl_list, nl_list, cs_list)

    def literals(self):
        pl_list, nl_list, _ = self.partition()
        return pl_list + nl_list

    def atoms(self):
        pl_list, _, _ = self.partition()
        return pl_list

    def negations(self):
        _, nl_list, _ = self.partition()
        return nl_list

    def constraints(self):
        _, _, cs_list = self.partition()
        return cs_list
