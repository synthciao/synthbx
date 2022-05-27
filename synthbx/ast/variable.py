from synthbx.ast.argument import Argument
from synthbx.env.const import EPrefix
import re


class Variable(Argument):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return str(self.name)

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.__str__() == other.__str__()
        else:
            TypeError()

    def __lt__(self, other):
        if isinstance(other, Variable):
            return self.__str__() < other.__str__()
        else:
            TypeError()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    def is_anonymous(self):
        if self.name == '_' \
                or re.match(re.escape(EPrefix.ANOVAR) + r'\d+', self.__str__()):
            return True
        return False


class AnonymousVariable(Variable):
    def __init__(self):
        super().__init__(name='_')
