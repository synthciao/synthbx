from synthbx.ast.clause import Clause
from synthbx.ast.atom import Atom
from synthbx.ast.negation import Negation
from synthbx.ast.constraint import Constraint
from synthbx.ast.conjunction import Conjunction
from synthbx.ast.variable import Variable, AnonymousVariable
from synthbx.ast.cmp import Cmp
from synthbx.env.const import EPrefix
from enum import Enum, auto, unique


@unique
class AtomicRule(Enum):
    NONATOMIC = auto()
    R_RULE = auto()
    U_RULE = auto()
    D_RULE = auto()
    I_RULE = auto()
    S_RULE = auto()
    P_RULE = auto()
    J_RULE = auto()
    C_RULE = auto()


class Rule(Clause):
    def __init__(self, head, body):
        self.head = head
        self.body = body

    def __str__(self):
        return f"{self.head} :- {'; '.join([str(conj) for conj in self.body])}."

    def __eq__(self, other):
        if isinstance(other, Rule):
            return self.head == other.head and self.body == other.body
        else:
            raise TypeError()

    def __lt__(self, other):
        if isinstance(other, Rule):
            return self.head < other.head \
                or (self.head == other.head and self.body < other.body)
        else:
            raise TypeError()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    def literals(self):
        ls = [self.head]
        for conj in self.body:
            ls += conj.literals()
        return ls

    def body_literals(self):
        ls = []
        for conj in self.body:
            ls += conj.literals()
        return ls

    def constraints(self):
        cs = []
        for conj in self.body:
            cs += conj.constraints()
        return cs

    def is_safe(self):
        return not self.not_safe()

    def not_safe(self):
        message = ''
        # Safety 1: head must have no anonymous variable
        if AnonymousVariable() in self.head.args:
            message += f"Unsupported: Rule {self.__str__()}"
            message += "\nHead has an anonymous variable !!"
            return message

        for conj in self.body:
            pl_list, nl_list, cs_list = conj.partition()

            pl_args, nl_args = set(), set()
            for l in pl_list:
                pl_args |= set(l.args)
            for l in nl_list:
                nl_args |= set(l.args)
            cs_args = {c.var for c in cs_list}

            # Safety 2: each argument of head must occur in body
            for a in self.head.args:
                if a not in pl_args | nl_args | cs_args:
                    message += f"Unsupported: Rule {self.__str__()}"
                    message += f"\n-- Variable {a} occurs in head but not in body !!"
                    return message

            # Safety 3: each non-anonymous variable that occurs in a negative literal of body must occur in at least one positive literal of body
            for a in nl_args:
                if not a.is_anonymous() and a not in pl_args:
                    message += f"Unsupported: Rule {self.__str__()}"
                    message += f"\n-- Variable {a} occurs in a negative literal but not occur in any positive literals of body !!"
                    return message

            # Safety 4: variable of a constraint in body must be non-anonymous
            # and either occur in a positive literal of body or be bound by an equality to a constant
            if AnonymousVariable() in cs_args:
                message += f"Unsupported: Rule {self.__str__()}"
                message += f"\n-- An anonymous variable occurs in a constraint of body !!"
                return message

            for cs in cs_list:
                if cs.var not in pl_args and cs.cmp != Cmp.EQ:
                    message += f"Unsupported: Rule {self.__str__()}"
                    message += f"\n-- Variable {cs.var} occurs in non-equality constraint {cs} but not in any positive literals of body !!"
                    return message

        return message

    def is_decomposable(self):
        return not self.not_decomposable()

    def not_decomposable(self):
        message = ''

        for conj in self.body:
            pl_list = conj.atoms()

            # 1. there is at least on positive literal in body
            if not pl_list:
                message += f"Unsupported: Rule {self.__str__()}"
                message += f"\n-- No positive literal in body !!"
                return message

            # 4. there should exists a join tree without cross-product
            if len(pl_list) > 1:
                for i, l in enumerate(pl_list):
                    l_args = [a for a in l.args if a != AnonymousVariable()]
                    remaining_args = set()
                    for j in range(len(pl_list)):
                        if j != i:
                            remaining_args |= set(pl_list[j].args)
                    common_args = [a for a in remaining_args
                                   if a != AnonymousVariable() and a in l_args]
                    if not common_args:
                        message += f"Unsupported: Rule {self.__str__()}"
                        message += f"\n-- Cannot make a join tree without cross-product !!"
                        return message

        # 2. all literals in rule are not nullaries
        literals = self.literals()

        for l in literals:
            if (type(l) is Atom and l.is_nullary()) \
                    or (type(l) is Negation and l.atom.is_nullary()):
                message += f"Unsupported: Rule {self.__str__()}"
                message += f"\n-- There is a nullary in rule !!"
                return message

        # 3. each literal in rule do not contain non-anonymous variables of same name
        for l in literals:
            for a in l.args:
                if a != AnonymousVariable() and l.args.count(a) > 1:
                    message += f"Unsupported: Rule {self.__str__()}"
                    message += f"\n-- Literal {l} contains two variables of name {a} !!"
                    return message

        return message

    def atype(self):
        if len(self.body) > 2:
            return AtomicRule.NONATOMIC

        # U_RULE
        if len(self.body) == 2:
            conj0, conj1 = self.body[0], self.body[1]
            if len(conj0.items) > 1 or len(conj1.items) > 1:
                return AtomicRule.NONATOMIC
            if conj0.items[0].args != conj1.items[0].args:
                return AtomicRule.NONATOMIC
            return AtomicRule.U_RULE

        conj = self.body[0]

        # R_RULE
        if len(conj.items) == 1 \
            and type(conj.items[0]) is Atom \
                and set(self.head.args) == set(conj.items[0].args):
            return AtomicRule.R_RULE

        # P_RULE
        if len(conj.items) == 1 \
            and type(conj.items[0]) is Atom \
                and set(self.head.args).issubset(set(conj.items[0].args)):
            return AtomicRule.P_RULE

        pl_list, nl_list, cs_list = conj.partition()

        # D_RULE
        if len(conj.items) == 2 \
            and len(pl_list) == 1 \
                and len(nl_list) == 1 \
        and self.head.args == pl_list[0].args \
        and self.head.args == nl_list[0].args:
            return AtomicRule.D_RULE

        # I_RULE & J_RULE
        if len(conj.items) == 2 \
                and len(pl_list) == 2:
            if self.head.args == pl_list[0].args \
                    and self.head.args == pl_list[1].args:
                return AtomicRule.I_RULE
            elif set(self.head.args) == set(pl_list[0].args) | set(pl_list[1].args):
                return AtomicRule.J_RULE

        # S_RULE & C_RULE
        if len(conj.items) >= 2 \
            and len(pl_list) == 1 \
                and not nl_list \
        and cs_list:
            cs_args = {c.var for c in cs_list}
            if cs_args.issubset(set(pl_list[0].args)) \
                    and self.head.args == pl_list[0].args:
                return AtomicRule.S_RULE
            if cs_args | set(pl_list[0].args) == set(self.head.args) \
                    and not cs_args.intersection(set(pl_list[0].args)):
                return AtomicRule.C_RULE

        # NONATOMIC
        return AtomicRule.NONATOMIC

    def is_flag_rule(self):
        return self.head.name.startswith(
            tuple([EPrefix.FLAG_R, EPrefix.FLAG_V])
        )

    def is_atomic(self):
        if self.atype() != AtomicRule.NONATOMIC:
            return True
        return False

    def is_of_atype(self, atype):
        return self.atype() == atype

    def is_id_rule(self):
        if self.atype() == AtomicRule.R_RULE:
            conj = self.body[0]
            if self.head.args == conj.items[0].args:
                return True
        return False

    def is_r_rule(self):
        return self.atype() == AtomicRule.R_RULE

    def is_u_rule(self):
        return self.atype() == AtomicRule.U_RULE

    def is_d_rule(self):
        return self.atype() == AtomicRule.D_RULE

    def is_i_rule(self):
        return self.atype() == AtomicRule.I_RULE

    def is_s_rule(self):
        return self.atype() == AtomicRule.S_RULE

    def is_p_rule(self):
        return self.atype() == AtomicRule.P_RULE

    def is_j_rule(self):
        return self.atype() == AtomicRule.J_RULE

    def is_c_rule(self):
        return self.atype() == AtomicRule.C_RULE
