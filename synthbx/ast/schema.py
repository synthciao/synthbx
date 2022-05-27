from synthbx.ast.unit import Unit


class Schema(Unit):
    def __init__(self, relations):
        self.relations = relations

    def __str__(self):
        return '\n'.join([str(r) for r in self.relations])

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    def input(self):
        return [r for r in self.relations if r.is_input()]

    def output(self):
        return [r for r in self.relations if r.is_output()]

    def invent(self):
        return [r for r in self.relations if r.is_invent()]

    def partition(self):
        source = [r for r in self.relations if r.is_input()]
        invent = [r for r in self.relations if r.is_invent()]
        view = [r for r in self.relations if r not in source and r not in invent]
        return source, view, invent
