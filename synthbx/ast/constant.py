from synthbx.ast.argument import Argument
from synthbx.env.const import ESymbol


class Constant(Argument):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())


class NumberConstant(Constant):
    def __init__(self, value):
        super().__init__(value=value)

    def __eq__(self, other):
        if isinstance(self, NumberConstant):
            return self.value == other.value
        else:
            raise TypeError()

    def __lt__(self, other):
        if isinstance(self, NumberConstant):
            return self.value < other.value
        else:
            raise TypeError()


class SymbolConstant(Constant):
    def __init__(self, value):
        super().__init__(value=value)

    def __eq__(self, other):
        if isinstance(self, SymbolConstant):
            return self.value == other.value
        else:
            raise TypeError()

    def __lt__(self, other):
        if isinstance(self, SymbolConstant):
            return self.value < other.value
        else:
            raise TypeError()


class NullConstant(SymbolConstant):
    def __init__(self):
        super().__init__(value=ESymbol.NULL)


class RejectConstant(SymbolConstant):
    def __init__(self):
        super().__init__(value=ESymbol.FLAG_R)


class ValidConstant(SymbolConstant):
    def __init__(self):
        super().__init__(value=ESymbol.FLAG_V)
