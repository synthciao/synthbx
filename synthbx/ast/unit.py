from copy import deepcopy


class Unit(object):
    def __init__(self):
        pass

    def clone(self):
        return deepcopy(self)
