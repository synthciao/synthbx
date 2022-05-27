from synthbx.ast.literal import Literal
from synthbx.ast.constant import RejectConstant, ValidConstant
from synthbx.env.const import EPrefix


class Atom(Literal):
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __str__(self):
        args_str = ', '.join([str(a) for a in self.args])
        return f'{self.name}({args_str})'

    def __eq__(self, other):
        if isinstance(other, Literal):
            return self.__str__() == other.__str__()
        else:
            raise TypeError()

    def __lt__(self, other):
        if isinstance(other, Atom):
            return self.__str__() < other.__str__()
        else:
            raise TypeError()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    def is_nullary(self):
        return not self.args

    def only_anonymous_variables(self):
        for a in self.args:
            if not a.is_anonymous():
                return False
        return True


class RejectAtom(Atom):
    def __init__(self):
        super().__init__(
            name=EPrefix.FLAG_R,
            args=[RejectConstant()]
        )


class ValidAtom(Atom):
    def __init__(self):
        super().__init__(
            name=EPrefix.FLAG_V,
            args=[ValidConstant()]
        )
