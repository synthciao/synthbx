from synthbx.ast.unit import Unit
from enum import Enum


class Type(Unit):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return str(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())


class PrimitiveType(Type):
    pass


class SymbolType(PrimitiveType):
    def __init__(self):
        super().__init__(name='symbol')


class NumberType(PrimitiveType):
    def __init__(self):
        super().__init__(name='number')


class SubType(Type):
    def __init__(self, name, base):
        super().__init__(name=name)
        self.base = base

    def str_of_decl(self):
        return f'.type {self.name} <: {self.base}'


class EquiType(Type):
    def __init__(self, name, alias):
        super().__init__(name=name)
        self.alias = alias

    def __eq__(self, other):
        if isinstance(other, EquiType):
            return self.name == other.name or self.alias == other.alias
        elif isinstance(other, PrimitiveType):
            return self.alias == other
        else:
            raise TypeError()

    def str_of_decl(self):
        return f'.type {self.name} = {self.alias}'


def const_by_type(v, t):
    if t == NumberType():
        return str(v)
    if t == SymbolType():
        return f'"{v}"'

    if type(t) is SubType:
        if t.base == NumberType():
            return str(v)
        if t.base == SymbolType():
            return f'"{v}"'

    if type(t) is EquiType:
        if t.alias == NumberType():
            return str(v)
        if t.alias == SymbolType():
            return f'"{v}"'
