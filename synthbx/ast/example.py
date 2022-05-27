from synthbx.ast.unit import Unit
from enum import Enum, unique, auto


class ExampleStatus(Enum):
    PROVIDED = auto()
    COMPUTED = auto()


class Example(Unit):
    def __init__(self, tables, status):
        self.tables = tables
        self.status = status

    def __str__(self):
        return '\n'.join([str(t) for t in self.tables])

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    def is_provided(self):
        return self.status == ExampleStatus.PROVIDED

    def is_computed(self):
        return self.status != ExampleStatus.PROVIDED

    def base_tables(self):
        return [t for t in tables if t.is_state_based()]

    def operation_tables(self):
        return [t for t in tables if t.is_operation_based()]

    def original_tables():
        return [t for t in tables if t.is_original()]

    def updated_tables():
        return [t for t in tables if t.is_updated()]

    def inserted_tables():
        return [t for t in tables if t.is_inserted()]

    def deleted_tables():
        return [t for t in tables if t.is_deleted()]
