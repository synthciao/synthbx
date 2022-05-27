from synthbx.ast.schema import Schema
from synthbx.ast.program import Program
from synthbx.ast.relation import Relation
from synthbx.ast.directive import Directive, DirectiveType
from synthbx.ast.rule import Rule, AtomicRule
from synthbx.ast.atom import Atom
from synthbx.ast.negation import Negation
from synthbx.ast.constraint import Constraint
from synthbx.ast.conjunction import Conjunction
from synthbx.ast.variable import Variable, AnonymousVariable
from synthbx.ast.constant import Constant
from synthbx.env.const import EPrefix, ESuffix
from synthbx.env.exception import NotSafeError, NotDecomposableError
from synthbx.util.list import mapin, mapto


counter = 0


def fresh_name():
    global counter
    counter += 1
    return f'{EPrefix.MIDDLE_REL}{counter}'


def preprocess(rule):
    fresh = -1
    for conj in rule.body:
        for l in conj.literals():
            for i, a in enumerate(l.args):
                if a == AnonymousVariable():
                    fresh += 1
                    l.args[i] = Variable(name=f'{EPrefix.ANOVAR}{fresh}')


def decompose(program):
    prog = program.clone()

    for rule in prog.rules:
        message = rule.not_safe()

        if message:
            raise NotSafeError(message)

        message = rule.not_decomposable()
        if message:
            raise NotDecomposableError(message)

    global counter
    counter = 0

    d0_u(prog)

    d_rules = []

    for rule in prog.rules:
        d1_rules, d1_relation_decls, d1_directives = decompose1(
            rule, prog.relation_decls, prog.directives
        )
        d_rules += d1_rules
        prog.add_relation_decls(d1_relation_decls)
        prog.add_directives(d1_directives)

    d7_u(d_rules, prog.relation_decls, prog.directives)

    d8_id(d_rules, prog.relation_decls, prog.directives)

    ren = []
    for rule in d_rules:
        ren.append(rename_variables(rule, prog.relation_decls))

    prog.rules = sorted(set(ren))

    return prog


def decompose1(rule, relation_decls, directives):

    if rule.is_atomic():
        return [rule], [], []

    preprocess(rule)

    d_rules_n = [[] for n in range(5)]
    d_relation_decls = []
    d_directives = []
    head = rule.head
    conj = rule.body[0]
    env = typing(rule, relation_decls)
    n = -1

    while True:
        d_rules_n[0], conj = d1_s(
            head, conj, d_relation_decls, d_directives, env)
        if Rule(head, [conj]).is_atomic():
            n = 0
            break
        d_rules_n[1], conj = d2_p(
            head, conj, d_relation_decls, d_directives, env)
        if Rule(head, [conj]).is_atomic():
            n = 1
            break
        d_rules_n[2], conj = d3_ji(
            head, conj, d_relation_decls, d_directives, env)
        if Rule(head, [conj]).is_atomic():
            n = 2
            break
        d_rules_n[3], conj = d4_p(
            head, conj, d_relation_decls, d_directives, env)
        if Rule(head, [conj]).is_atomic():
            n = 3
            break
        d_rules_n[4], conj = d5_jd(
            head, conj, d_relation_decls, d_directives, env)
        n = 4
        break

    d_rules = [Rule(head=head, body=[conj])]
    for i in range(n+1):
        d_rules += d_rules_n[i]

    d6_id(head, conj, d_rules, d_relation_decls, d_directives, env)

    return d_rules, d_relation_decls, d_directives


def d0_u(prog):
    for rule in prog.rules:
        if len(rule.body) == 1:
            continue

        d_rules = []
        for conj in rule.body:
            d_rules.append(
                Rule(
                    head=rule.head,
                    body=[conj]
                ).clone()
            )

        prog.rules.remove(rule)
        prog.rules += d_rules


def d1_s(head, conj, d_relation_decls, d_directives, env):
    global counter

    dr = []

    pl_list, nl_list, cs_list = conj.partition()
    if not cs_list:
        return dr, conj

    pl_list_0, nl_list_0, cs_list_0 = conj.clone().partition()

    for l in pl_list_0 + nl_list_0:
        i = pl_list.index(l) if l in pl_list_0 else nl_list.index(l)

        cs_l = [c for c in cs_list_0 if c.var in l.args]
        if not cs_l:
            continue
        cs_list = [c for c in cs_list if c not in cs_l]
        f = fresh_name()
        l_f = Atom(
            name=f,
            args=l.args
        ).clone()
        add_d_units(d_relation_decls, d_directives, l_f, env)
        if l in pl_list_0:
            dr.append(
                Rule(
                    head=l_f,
                    body=[Conjunction(items=[l] + cs_l)]
                ).clone()
            )
            pl_list[i] = l_f
        else:
            dr.append(
                Rule(
                    head=l_f,
                    body=[Conjunction(items=[l.atom] + cs_l)]
                ).clone()
            )
            nl_list[i] = Negation(atom=l_f).clone()

    conj.items = pl_list + nl_list + cs_list

    return dr, conj


def d2_p(head, conj, d_relation_decls, d_directives, env):
    global counter

    dr = []

    pl_list, nl_list, cs_list = conj.partition()

    var_list = []
    for l in [head] + pl_list + nl_list:
        var_list += l.args

    for l in pl_list + nl_list:
        i = pl_list.index(l) if l in pl_list else nl_list.index(l)

        p = [a for a in l.args if var_list.count(a) == 1]
        if not p:
            continue
        f = fresh_name()
        l_f = Atom(
            name=f,
            args=[a for a in l.args if a not in p]
        ).clone()
        add_d_units(d_relation_decls, d_directives, l_f, env)
        if l in pl_list:
            dr.append(
                Rule(
                    head=l_f,
                    body=[Conjunction(items=[l])]
                ).clone()
            )
            pl_list[i] = l_f
        else:
            dr.append(
                Rule(
                    head=l_f,
                    body=[Conjunction(items=[l.atom])]
                ).clone()
            )
            nl_list[i] = Negation(atom=l_f).clone()

    conj.items = pl_list + nl_list + cs_list

    return dr, conj


def d3_ji(head, conj, d_relation_decls, d_directives, env):
    global counter

    dr = []

    pl_list, nl_list, cs_list = conj.partition()

    if len(pl_list) == 1:
        return dr, conj

    while len(pl_list) > 1:
        l1 = pl_list.pop(0)
        l2 = [l for l in pl_list
              if set(l1.args).intersection(set(l.args))][0]
        f = fresh_name()
        l_f = Atom(
            name=f,
            args=sorted(set(l1.args) | set(l2.args))
        ).clone()
        add_d_units(d_relation_decls, d_directives, l_f, env)
        dr.append(
            Rule(
                head=l_f,
                body=[Conjunction(items=[l1, l2])]
            ).clone()
        )
        pl_list.remove(l2)
        pl_list.insert(0, l_f)

    conj.items = pl_list + nl_list + cs_list

    return dr, conj


def d4_p(head, conj, d_relation_decls, d_directives, env):
    global counter

    dr = []

    pl_list, nl_list, cs_list = conj.partition()

    l = pl_list[0]
    nl_args = {v for nl in nl_list for v in nl.args}
    p = [v for v in l.args
         if v not in head.args and v not in nl_args
         ]

    if not p:
        return dr, conj

    f = fresh_name()
    l_f = Atom(
        name=f,
        args=[a for a in l.args if a not in p]
    ).clone()
    add_d_units(d_relation_decls, d_directives, l_f, env)
    dr.append(
        Rule(
            head=l_f,
            body=[Conjunction(items=[l])]
        ).clone()
    )
    pl_list[0] = l_f

    conj.items = pl_list + nl_list + cs_list

    return dr, conj


def d5_jd(head, conj, d_relation_decls, d_directives, env):
    global counter

    dr = []

    pl_list, nl_list, cs_list = conj.partition()
    while nl_list:
        l1 = pl_list.pop(0)
        l2 = nl_list.pop(0)
        if l1.args != l2.args:
            f1 = fresh_name()
            f2 = fresh_name()
            l_f1 = Atom(
                name=f1,
                args=l1.args
            ).clone()
            l_f2 = Atom(
                name=f2,
                args=l1.args
            ).clone()
            add_d_units(d_relation_decls, d_directives, l_f1, env)
            add_d_units(d_relation_decls, d_directives, l_f2, env)
            dr.append(
                Rule(
                    head=l_f1,
                    body=[Conjunction(items=[l1, l2.atom])]
                ).clone()
            )
            dr.append(
                Rule(
                    head=l_f2,
                    body=[Conjunction(items=[l1, Negation(atom=l_f1)])]
                ).clone()
            )
            pl_list.append(l_f2)
        else:
            f = fresh_name()
            l_f = Atom(
                name=f,
                args=l1.args
            ).clone()
            add_d_units(d_relation_decls, d_directives, l_f, env)
            dr.append(
                Rule(
                    head=l_f,
                    body=[Conjunction(items=[l1, l2])]
                ).clone()
            )
            pl_list.append(l_f)

    conj.items = pl_list + nl_list + cs_list

    return dr, conj


def d6_id(head, conj, d_rules, d_relation_decls, d_directives, env):
    if Rule(head, [conj]).is_id_rule():
        l = conj.items[0]
        for i, r in enumerate(d_rules):
            if r.head == l:
                remove_d_units(d_relation_decls, d_directives, r.head, env)
                d_rules[i] = Rule(
                    head=head,
                    body=r.body
                ).clone()
        d_rules.remove(Rule(head, [conj]))


def d7_u(d_rules, d_relation_decls, d_directives):
    def fresh_u_name(name):
        nonlocal counter
        counter += 1
        return f'{name}__{counter}_'

    head_name_set = {r.head.name for r in d_rules}
    g_dict = {name: [] for name in head_name_set}

    for r in d_rules:
        g_dict[r.head.name].append(r)

    for k in g_dict:
        if len(g_dict[k]) == 1:
            continue

        counter = -1

        [d_rules.remove(r) for r in g_dict[k]]

        rd_k = [rd for rd in d_relation_decls if rd.name == k][0]
        args_k = rd_k.args()
        l_k = Atom(
            name=k,
            args=args_k
        ).clone()

        s1 = [r for r in g_dict[k] if r.is_id_rule()]
        s2 = [r for r in g_dict[k] if r not in s1]

        while s2:
            r = s2.pop(0)
            f = fresh_u_name(k)
            l_f = Atom(
                name=f,
                args=r.head.args
            ).clone()
            env = typing(r, d_relation_decls)
            add_d_units(d_relation_decls, d_directives, l_f, env)
            d_rules.append(
                Rule(
                    head=l_f,
                    body=r.body
                ).clone()
            )
            l_f = Atom(
                name=f,
                args=args_k
            ).clone()
            s1.append(
                Rule(
                    head=l_k,
                    body=[Conjunction(items=[l_f])]
                ).clone()
            )

        while len(s1) > 2:
            r0 = s1.pop(0)
            r1 = s1.pop(0)
            f = fresh_u_name(k)
            l_f = Atom(
                name=f,
                args=args_k
            ).clone()
            env = typing(r0, d_relation_decls)
            add_d_units(d_relation_decls, d_directives, l_f, env)
            d_rules.append(
                Rule(
                    head=l_f,
                    body=r0.body + r1.body
                ).clone()
            )
            s1.append(
                Rule(
                    head=l_k,
                    body=[Conjunction(items=[l_f])]
                ).clone()
            )

        if len(s1) == 2:
            r0 = s1.pop(0)
            r1 = s1.pop(0)
            d_rules.append(
                Rule(
                    head=r0.head,
                    body=r0.body + r1.body
                ).clone()
            )


def d8_id(d_rules, d_relation_decls, d_directives):
    def fresh_r_name(name):
        nonlocal counter
        counter += 1
        return f'{name}_{counter}{ESuffix.ALIAS}'

    rds_names = {rd.name for rd in d_relation_decls}
    g_dict = {name: set() for name in rds_names}
    # g_dict uses values of <set> to remove duplicates

    for r in d_rules:
        for l in r.body_literals():
            g_dict[l.name].add(r)

    for k in g_dict:
        if len(g_dict[k]) == 1:
            continue

        rd_k = [rd for rd in d_relation_decls
                if rd.name == k][0]
        args_k = rd_k.args()
        l_k = Atom(
            name=k,
            args=args_k
        ).clone()

        counter = -1

        visited = {r: False for r in g_dict[k]}

        for r in g_dict[k]:
            # if r.body contains only 1 atom and nothing else => continue
            # otherwise => make an alias of relation of name k

            if visited[r]:
                continue

            if r.is_r_rule() or r.is_s_rule() or r.is_p_rule():
                visited[r] = True
                continue

            for conj in r.body:
                for i, item in enumerate(conj.items):
                    if type(item) is not Constraint and item.name == k:
                        f = fresh_r_name(k)
                        l_f = Atom(
                            name=f,
                            args=args_k
                        ).clone()

                        d_relation_decls.append(
                            Relation(
                                name=f,
                                schema=rd_k.schema
                            ).clone()
                        )

                        d_directives.append(
                            Directive(
                                type=DirectiveType.OUTPUT,
                                name=f
                            ).clone()
                        )

                        d_rules.append(
                            Rule(
                                head=l_f,
                                body=[Conjunction(items=[l_k])]
                            ).clone()
                        )

                        if type(item) is Atom:
                            conj.items[i] = Atom(
                                name=f,
                                args=item.args
                            ).clone()
                        else:
                            conj.items[i] = Negation(atom=Atom(
                                name=f,
                                args=item.args
                            )).clone()


def typing(rule, relation_decls):
    literals = rule.literals()
    variables = set()

    for l in literals:
        variables |= set(l.args)

    variables = sorted(variables)

    env = {v: None for v in variables}

    for v in variables:
        for l in literals:
            if v in l.args:
                v_index = l.args.index(v)
                for rd in relation_decls:
                    if rd.name == l.name:
                        env[v] = rd.schema[v_index]
                        break
                break
    return env


def add_d_units(d_relation_decls, d_directives, new_literal, env):
    d_relation_decls.append(
        Relation(
            name=new_literal.name,
            schema=[env[v] for v in new_literal.args]
        ).clone()
    )
    d_directives.append(
        Directive(
            type=DirectiveType.OUTPUT,
            name=new_literal.name
        ).clone()
    )


def remove_d_units(d_relation_decls, d_directives, old_literal, env):
    for rd in d_relation_decls:
        if rd.name == old_literal.name:
            d_relation_decls.remove(rd)

    for d in d_directives:
        if d.name == old_literal.name:
            d_directives.remove(d)


def rename_variables(rule, relation_decls):
    """
    rename variables in rule to (v0, v1, ..., vN)

    Args:
        rule (_type_): _description_
        relation_decls (_type_): _description_
    """

    func_name = 'rename_variables_' + rule.atype().name[0].lower()
    return globals()[func_name](rule, relation_decls)


def rename_variables_r(rule, relation_decls):
    """
    view(v(p(0)), v(p(1))..., v(p(N))) :- source(v0, v1, ..., vN)
    """
    view = rule.head
    source = rule.body[0].items[0]

    rd = [rd for rd in relation_decls if rd.name == source.name][0]

    if source.args == rd.args():
        return rule

    map0 = mapin(view.args, source.args)

    rule = Rule(
        head=Atom(
            name=view.name,
            args=mapto(rd.args(), map0)
        ),
        body=[Conjunction(items=[
            Atom(
                name=source.name,
                args=rd.args()
            )
        ])]
    ).clone()

    return rule


def rename_variables_u(rule, relation_decls):
    """
    view(v0, v1, ..., vN) :- source0(v0, v1, ..., vN); source1(v0, v1, ..., vN).
    """
    view = rule.head

    rd = [rd for rd in relation_decls if rd.name == view.name][0]

    if view.args == rd.args():
        return rule

    source0 = rule.body[0].items[0]
    source1 = rule.body[1].items[0]

    rule = Rule(
        head=Atom(
            name=view.name,
            args=rd.args()
        ),
        body=[
            Conjunction(items=[
                Atom(
                    name=source0.name,
                    args=rd.args()
                )
            ]),
            Conjunction(items=[
                Atom(
                    name=source1.name,
                    args=rd.args()
                )
            ])
        ]
    ).clone()

    return rule


def rename_variables_d(rule, relation_decls):
    """
    view(v0, v1, ..., vN) :- source0(v0, v1, ..., vN), !source1(v0, v1, ..., vN).
    """
    view = rule.head

    rd = [rd for rd in relation_decls if rd.name == view.name][0]

    if view.args == rd.args():
        return rule

    source0 = rule.body[0].items[0]
    source1 = rule.body[0].items[1]

    rule = Rule(
        head=Atom(
            name=view.name,
            args=rd.args()
        ),
        body=[Conjunction(items=[
            Atom(
                name=source0.name,
                args=rd.args()
            ),
            Negation(atom=Atom(
                name=source1.name,
                args=rd.args()
            ))
        ])]
    ).clone()

    return rule


def rename_variables_i(rule, relation_decls):
    """
    view(v0, v1, ..., vN) :- source0(v0, v1, ..., vN), source1(v0, v1, ..., vN).
    """
    view = rule.head

    rd = [rd for rd in relation_decls if rd.name == view.name][0]

    if view.args == rd.args():
        return rule

    source0 = rule.body[0].items[0]
    source1 = rule.body[0].items[1]

    rule = Rule(
        head=Atom(
            name=view.name,
            args=rd.args()
        ),
        body=[
            Conjunction(items=[
                Atom(
                    name=source0.name,
                    args=rd.args()
                ),
                Atom(
                    name=source1.name,
                    args=rd.args()
                )
            ])]
    ).clone()

    return rule


def rename_variables_s(rule, relation_decls):
    """
    view(v0, v1, ..., vN) :- source(v0, v1, ..., vN), v(c0) -cmp- c0, ..., v(cM) -cmp- cM.
    """
    view = rule.head
    source = rule.body[0].items[0]

    rd = [rd for rd in relation_decls if rd.name == source.name][0]

    if source.args == rd.args():
        return rule

    constraints = rule.body[0].items[1:]
    cs_var = [c.var for c in constraints]

    map0 = mapin(cs_var, source.args)

    n_cs_var_index = mapto(rd.args(), map0)

    n_constraints = []
    for i, c in enumerate(constraints):
        n_constraints.append(
            Constraint(
                cmp=c.cmp,
                var=n_cs_var_index[i],
                const=c.const
            ).clone()
        )

    rule = Rule(
        head=Atom(
            name=view.name,
            args=rd.args()
        ),
        body=[
            Conjunction(items=[
                Atom(
                    name=source.name,
                    args=rd.args()
                )
            ] + n_constraints
            )]
    ).clone()

    return rule


def rename_variables_p(rule, relation_decls):
    """
    view(v(p(0)), v(p(1)), ..., v(p(M)) :- source(v0, v1, ..., vN).
    """
    view = rule.head
    source = rule.body[0].items[0]

    rd = [rd for rd in relation_decls if rd.name == source.name][0]

    if source.args == rd.args():
        return rule

    map0 = mapin(view.args, source.args)

    rule = Rule(
        head=Atom(
            name=view.name,
            args=mapto(rd.args(), map0)
        ),
        body=[Conjunction(items=[
            Atom(
                name=source.name,
                args=rd.args()
            )
        ])]
    ).clone()

    return rule


def rename_variables_j(rule, relation_decls):
    """
    view(v0, v1, ..., vN) :- source0(v(p(0), ..., v(p(K)), source1(v(p(K+1)), ..., v(p(N)))
    """
    view = rule.head
    source0 = rule.body[0].items[0]
    source1 = rule.body[0].items[1]

    rd = [rd for rd in relation_decls if rd.name == view.name][0]

    if view.args == rd.args():
        return rule

    map0 = mapin(source0.args, view.args)
    map1 = mapin(source1.args, view.args)

    rule = Rule(
        head=Atom(
            name=view.name,
            args=rd.args()
        ),
        body=[
            Conjunction(items=[
                Atom(
                    name=source0.name,
                    args=mapto(rd.args(), map0)
                ),
                Atom(
                    name=source1.name,
                    args=mapto(rd.args(), map1)
                )
            ])]
    ).clone()

    return rule


def rename_variables_c(rule, relation_decls):
    """
    view(v0, v1, ..., vN) :- source(v0, v1, ..., vK), v(K+1) = c(K+1), ..., vN = cN
    """
    view = rule.head
    source = rule.body[0].items[0]

    rd = [rd for rd in relation_decls if rd.name == view.name][0]

    if view.args == rd.args():
        return rule

    constraints = rule.body[0].items[1:]
    cs_var = [c.var for c in constraints]

    map0 = mapin(source.args, view.args)
    map1 = mapin(cs_var, view.args)

    n_cs_var_index = mapto(rd.args(), map1)

    n_constraints = []
    for i, c in enumerate(constraints):
        n_constraints.append(
            Constraint(
                cmp=c.cmp,
                var=n_cs_var_index[i],
                const=c.const
            ).clone()
        )

    rule = Rule(
        head=Atom(
            name=view.name,
            args=rd.args()
        ),
        body=[
            Conjunction(items=[
                Atom(
                    name=source.name,
                    args=mapto(rd.args(), map0)
                )
            ] + n_constraints
            )]
    ).clone()

    return rule


if __name__ == '__main__':
    from synthbx.parser.program.parser import parse_program
    from synthbx.util.io import yprint, cprint

    sql = 'embeded'
    data = ''

    try:
        import sys
        sql = sys.argv[1]
        data = open(f'{sql}', 'r').read()
    except:
        data = '''
            .type id <: symbol
            .type size <: symbol
            .type bid <: symbol
            .type name <: symbol
            .decl vview(v0: id, v1: size, v2: name, v3: desc)

            .input brand, vehicle

            .input temp1
            .input temp2

            .decl brand(v0: bid, v1: name)
            .decl vehicle(v0: id, v1: size, v2: bid)
            .decl temp1(v0: id, v1: size, v2: name)
            .decl temp2(v0: id, v1: size, v2: name)

            .output vview

            vview(v0, v1, v2, v3) :-
                vehicle(v0, v1, v4), brand(v4, v2),
                !temp1(v0, v1, _), !temp2(v0, _, _),
                v1 = "100", v3 = "null".
        '''

        data = '''
        .type sid <: symbol
.type name <: symbol
.type city <: symbol
.type active <: symbol
.type cid <: symbol

.decl staffs(v0: sid, v1: name, v2: city, v3: active)
.decl customers(v0: cid, v1: name, v2: city)
.decl tokyoac(v0: name)
.decl inv0_staffs(v0: sid, v1: name, v2: city, v3: active)
.decl inv1_staffs(v0: sid, v1: name, v2: city, v3: active)
.decl inv2_staffs(v0: sid, v1: name, v2: city, v3: active)
.decl inv0_customers(v0: cid, v1: name, v2: city)

.input staffs
.input customers
.output tokyoac
.output inv0_staffs
.output inv1_staffs
.output inv2_staffs
.output inv0_customers

inv0_customers(v0, v1, v2) :- customers(v0, v1, v2), v2 = "Tokyo".
inv1_staffs(v0, v1, v2, v3) :- staffs(v0, v1, v2, v3), v3 = "1".
tokyoac(v0) :- inv1_staffs(v2, v0, v3, v6), inv0_customers(v5, v1, v3).
tokyoac(v2) :- inv0_customers(v0, v2, v1), !inv0_staffs(_, _, v1, _).
        '''

    prog = parse_program(data)

    d_prog = decompose(prog)

    print(f'============== {sql}.dl ==============')
    print('[+] ------- OLD -------')
    yprint(prog)
    print('[+] ------- NEW -------')
    cprint(d_prog)
