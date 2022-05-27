from synthbx.ast.unit import Unit
from enum import Enum


class DirectiveType(Enum):
    INPUT = '.input'
    OUTPUT = '.output'


class Directive(Unit):
    def __init__(self, type, name):
        self.type = type
        self.name = name

    def __str__(self):
        return f'{self.type.value} {self.name}'

    def __eq__(self, other):
        if isinstance(other, Directive):
            return self.__str__() == other.__str__()
        else:
            raise TypeError()

    def __lt__(self, other):
        if isinstance(other, Directive):
            return self.__str__() < other.__str__()
        else:
            raise TypeError()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    def is_input(self):
        return self.type == DirectiveType.INPUT

    def is_output(self):
        return self.type == DirectiveType.OUTPUT
