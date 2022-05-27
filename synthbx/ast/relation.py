from synthbx.ast.unit import Unit
from synthbx.ast.type import SymbolType
from synthbx.ast.directive import DirectiveType
from synthbx.ast.variable import Variable
from synthbx.env.const import EPrefix


class Relation(Unit):
    def __init__(self, name, schema, directives=[DirectiveType.OUTPUT], invent=True):
        self.name = name
        self.schema = schema
        self.directives = directives
        self.invent = invent

    def __str__(self):
        schema_str = ', '.join([str(t) for t in self.schema])
        return f'{self.name}({schema_str})'

    def __eq__(self, other):
        if isinstance(other, Relation):
            return self.__str__() == other.__str__()
        else:
            raise TypeError()

    def __lt__(self, other):
        if isinstance(other, Relation):
            return self.__str__() < other.__str__()
        else:
            raise TypeError()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    def str_of_schema(self):
        sym = ''
        if self.directives == [DirectiveType.INPUT]:
            sym = '*'
        elif self.invent:
            sym = '+'
        schema_str = ', '.join([str(t) for t in self.schema])
        return f'{sym}{self.name}({schema_str})'

    def str_of_decl(self):
        schema_str = ', '.join([
            f'{EPrefix.VAR}{i}: {self.schema[i]}'
            for i in range(len(self.schema))
        ])
        return f'.decl {self.name}({schema_str})'

    def is_input(self):
        return DirectiveType.INPUT in self.directives

    def is_output(self):
        return DirectiveType.OUTPUT in self.directives

    def is_invent(self):
        return self.invent == True

    def is_of_schema(self, schema):
        return self in schema.relations

    def args(self):
        return [
            Variable(name=f'{EPrefix.VAR}{i}')
            for i in range(len(self.schema))
        ]

    def add_directive(self, directive):
        if directive not in self.directives:
            if directive == DirectiveType.INPUT:
                self.directives.insert(0, directive)
            else:
                self.directives.append(directive)

    def remove_directive(self, directive):
        if directive in self.directives:
            self.directives.remove(directive)

    def clear_directives(self):
        self.directives = []


class RejectRelation(Relation):
    def __init__(self):
        super().__init__(name=EPrefix.FLAG_R, schema=[SymbolType()])


class ValidRelation(Relation):
    def __init__(self):
        super().__init__(name=EPrefix.FLAG_V, schema=[SymbolType()])
