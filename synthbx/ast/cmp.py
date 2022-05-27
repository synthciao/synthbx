from enum import Enum


class Cmp(Enum):
    EQ = '='
    NE = '!='
    LT = '<'
    GT = '>'
    LE = '<='
    GE = '>='

    @classmethod
    def negate(self, cmp):
        c = [Cmp.EQ, Cmp.NE, Cmp.LT, Cmp.GT, Cmp.LE, Cmp.GE]
        nc = [Cmp.NE, Cmp.EQ, Cmp.GE, Cmp.LE, Cmp.GT, Cmp.LT]
        return nc[c.index(cmp)]
