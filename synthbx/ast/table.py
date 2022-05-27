from synthbx.ast.unit import Unit
from enum import Enum, auto, unique


@unique
class TableBase(Enum):
    STATE = auto()
    OPERATION = auto()


@unique
class TableStatus(Enum):
    ORIGINAL = auto()
    UPDATED = auto()
    INSERTED = auto()
    DELETED = auto()


class Table(Unit):
    def __init__(self, name, types, base, status, data):
        self.name = name
        self.types = types
        self.base = base
        self.status = status
        self.data = data

    def __str__(self):
        out = f'{self.name}[{self.status}]({self.types})\n'
        for row in self.data:
            out += f'{row}\n'
        return out

    def __eq__(self, other):
        if isinstance(other, Table):
            return self.name == other.name \
                and self.types == other.types \
                and self.data == other.data
        else:
            raise TypeError()

    def __lt__(self, other):
        if isinstance(other, Table):
            return self.name < other.name \
                or self.types < other.types \
                or self.data < other.data
        else:
            raise TypeError()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    def is_state_based(self):
        return self.base == TableBase.STATE

    def is_operation_based(self):
        return self.base == TableBase.OPERATION

    def is_original(self):
        return self.is_state_based() and self.status == TableStatus.ORIGINAL

    def is_updated(self):
        return self.is_state_based() and self.status == TableStatus.UPDATED

    def is_inserted(self):
        return self.is_operation_based() and self.status == TableStatus.INSERTED

    def is_deleted(self):
        return self.is_operation_based() and self.status == TableStatus.DELETED

    def sort_data(self):
        self.data = sorted(self.data)
