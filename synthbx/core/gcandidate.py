from synthbx.ast.program import Program
from synthbx.ast.type import Type, NumberType, SymbolType, SubType, const_by_type
from synthbx.ast.relation import Relation, RejectRelation, ValidRelation
from synthbx.ast.directive import Directive, DirectiveType
from synthbx.ast.rule import Rule, AtomicRule
from synthbx.ast.fact import Fact
from synthbx.ast.atom import Atom, RejectAtom, ValidAtom
from synthbx.ast.negation import Negation
from synthbx.ast.constraint import Constraint
from synthbx.ast.conjunction import Conjunction
from synthbx.ast.cmp import Cmp
from synthbx.ast.variable import Variable, AnonymousVariable
from synthbx.ast.constant import Constant, NullConstant

from synthbx.util.io import yprint, cprint

import itertools
import re
import copy


def gen_get_cand(example, schema_partition):
    def fresh_inv(name):
        nonlocal i_counter
        i_counter += 1
        return f'inv{i_counter}_{name}'

    def fresh_var():
        nonlocal v_counter
        v_counter += 1
        return Variable(name=f'v{v_counter}')

    prog = Program(
        type_decls=[],
        relation_decls=[],
        directives=[],
        rules=[]
    )

    source, view, invent = copy.deepcopy(schema_partition)
    inputs = source
    outputs = view + invent

    max_n_body_pl = 2
    max_n_body_nl = 1
    max_n_body_cs = 2
    max_n_self_join = 0

    if len(invent) > 1:
        max_n_body_nl = 0

    if len(source) > 3:
        max_n_body_pl = len(source) - 1
        max_n_body_nl = 0
        max_n_body_cs = 1

    n_invents = []

    # type_decls
    for r in inputs + outputs:
        for t in r.schema:
            if t != SymbolType() or t != NumberType():
                prog.add_type_decl(
                    SubType(
                        name=t.name,
                        base=SymbolType()
                    ).clone()
                )

    # relation_decls
    prog.add_relation_decls(inputs + outputs)

    # directives
    for rd in prog.relation_decls:
        prog.add_directive(
            Directive(
                type=rd.directives[0],
                name=rd.name
            ).clone()
        )

    # rules

    # reserved_string_from_example
    t_list = set()
    for rd in prog.relation_decls:
        t_list |= set(rd.schema)

    const_dict = {}
    for t in t_list:
        const_dict[t] = set()

    for inp in inputs:
        table_original = [t for t in example.tables
                          if t.name == inp.name and t.is_original()
                          ][0]
        table_update = [t for t in example.tables
                        if t.name == inp.name and t.is_updated()
                        ][0]
        data = [r for r in table_original.data if r not in table_update.data] + \
            [r for r in table_update.data if r not in table_original.data]

        for r in data:
            for i, _ in enumerate(r):
                const_dict[inp.schema[i]].add(r[i])

    t_pop = [t for t in const_dict
             if re.match(r'.*(?:id|name|date|text|key).*', t.name)]
    [const_dict.pop(t) for t in t_pop]

    max_constants_t1 = 30
    max_constants_t2 = 50

    l = 0
    for t in const_dict:
        l += len(const_dict[t])
    if l > max_constants_t1:
        if l < max_constants_t2:
            max_n_body_cs = 1
        else:
            max_n_body_cs = 0

    # cmp_ops = [Cmp.EQ, Cmp.NE]
    cmp_ops = [Cmp.EQ]

    for inp in inputs:
        i_counter = -1

        if len(set(inp.schema)) < len(inp.schema):
            for i in range(max_n_self_join):
                f = fresh_inv(inp.name)
                rd = inp.clone()
                rd.name = f
                prog.add_relation_decl(rd)
                n_invents.append(rd)

                prog.add_directive(
                    Directive(
                        type=DirectiveType.OUTPUT,
                        name=f
                    ).clone()
                )

                prog.add_rule(
                    Rule(
                        head=Atom(
                            name=f,
                            args=inp.args()
                        ),
                        body=[Conjunction(items=[
                            Atom(
                                name=inp.name,
                                args=inp.args()
                            )]
                        )]
                    ).clone()
                )

        ts = [t for t in inp.schema if t in const_dict and const_dict[t]]

        if not ts:
            continue

        if max_n_body_cs > 0:
            f = fresh_inv(inp.name)
            rd = inp.clone()
            rd.name = f
            prog.add_relation_decl(rd)
            n_invents.append(rd)

            prog.add_directive(
                Directive(
                    type=DirectiveType.OUTPUT,
                    name=f
                ).clone()
            )

        for n in range(1, max_n_body_cs + 1):
            for comb_i in itertools.combinations(range(len(inp.schema)), n):
                f_continue = False
                for i in comb_i:
                    if inp.schema[i] not in ts:
                        f_continue = True

                if f_continue:
                    continue

                constraints = []

                for i in comb_i:
                    cs = []
                    for p in itertools.product(cmp_ops, const_dict[inp.schema[i]]):
                        cs.append(
                            Constraint(
                                cmp=p[0],
                                var=inp.args()[i],
                                const=const_by_type(p[1], inp.schema[i])
                            )
                        )
                    constraints.append(cs)

                for cs in itertools.product(*constraints):
                    prog.add_rule(
                        Rule(
                            head=Atom(
                                name=f,
                                args=inp.args()
                            ),
                            body=[Conjunction(items=[
                                Atom(
                                    name=inp.name,
                                    args=inp.args()
                                )
                            ] + list(cs)
                            )]
                        ).clone()
                    )

    inputs += n_invents

    for outp in outputs:
        body_items = copy.deepcopy(
            [rd for rd in inputs + invent if rd != outp]
        )

        body_pls = sum(
            [list(itertools.combinations(body_items, i))
             for i in range(1, max_n_body_pl + 1)],
            []
        )
        body_nls = sum(
            [list(itertools.combinations(body_items, i))
             for i in range(0, max_n_body_nl + 1)],
            []
        )

        for (pls, nls) in itertools.product(body_pls, body_nls):
            type_pls = [t for pl in pls for t in pl.schema]
            type_nls = {t for nl in nls for t in nl.schema}

            if not set(outp.schema).issubset(set(type_pls)):
                continue

            rd_names = [rd.name for rd in list(pls) + list(nls)]

            rd_names = [n[n.index('_')+1:] if re.match(r'inv\d+_(.*)', n) else n
                        for n in rd_names
                        ]

            m_sj_flag = False

            for n in set(rd_names):
                if rd_names.count(n) > max_n_self_join + 1:
                    m_sj_flag = True
                    break

            if m_sj_flag:
                continue

            v_counter = -1

            v_dict = {t: [] for t in set(type_pls) | set(type_nls)}
            for t in set(type_pls):
                for i in range(type_pls.count(t)):
                    fv = fresh_var()
                    v_dict[t].append(fv)

            literals = {rd: [] for rd in [outp] + list(pls) + list(nls)}

            literals = {i: [] for i in range(1 + len(pls) + len(nls))}

            for i in literals:
                name = None
                args_dict = None
                if i == 0:
                    name = outp.name
                    args_dict = {j: v_dict[t]
                                 for j, t in enumerate(outp.schema)
                                 }
                elif i < len(pls) + 1:
                    name = pls[i-1].name
                    args_dict = {j: v_dict[t]
                                 for j, t in enumerate(pls[i-1].schema)
                                 }
                else:
                    name = nls[i-len(pls)-1].name
                    args_dict = {j: [AnonymousVariable()] + v_dict[t]
                                 for j, t in enumerate(nls[i-len(pls)-1].schema)
                                 }

                for args in itertools.product(*args_dict.values()):
                    literals[i].append(
                        Atom(
                            name=name,
                            args=list(args)
                        ).clone()
                    )

            for comb in itertools.product(*literals.values()):
                h = comb[0]
                pl = list(comb[1:len(pls)+1])
                nl = [Negation(atom=l) for l in comb[len(pls)+1:]]

                oav_flag = False
                for l in nl:
                    if l.atom.only_anonymous_variables():
                        oav_flag = True
                        break

                if oav_flag:
                    continue

                pl_args = set(h.args) | {a for l in pl for a in l.args}
                for i, l in enumerate(nl):
                    if not set(l.args).issubset(pl_args):
                        l_args = l.args
                        for ia, a in enumerate(l_args):
                            if a not in pl_args and not a.is_anonymous():
                                l_args[ia] = AnonymousVariable()
                        nl[i] = Negation(atom=Atom(
                            name=l.name,
                            args=l_args
                        )).clone()

                rule = Rule(
                    head=h,
                    body=[Conjunction(items=pl + nl)]
                ).clone()

                if rule.is_safe() and rule.is_decomposable():
                    prog.add_rule(rule)

    # process for rule selection
    prog.add_relation_decl(
        Relation(
            name='Rule',
            schema=[NumberType()]
        ).clone()
    )

    prog.add_directive(
        Directive(
            type=DirectiveType.INPUT,
            name='Rule',
        ).clone()
    )

    count = -1
    for r in prog.rules:
        count += 1
        r.body[0].items.append(
            Atom(
                name='Rule',
                args=[Constant(value=count)]
            ).clone()
        )

    return prog, count + 1


if __name__ == '__main__':
    from synthbx.env.const import EFolder
    from synthbx.util.io import cprint, yprint
    import sys

    # path = sys.arv[1]
    path = 'tests/data/tokyoac'
    sc_path = f'{path}/{EFolder.SCHEMA}'
    ex_path = f'{path}/{EFolder.EXAMPLE}'

    from synthbx.core.synthesize import parse_specification
    schema, example = parse_specification(sc_path, ex_path)

    schema_partition = schema.partition()
    p, _ = gen_get_cand(example, schema_partition)
    for r in p.rules:
        yprint(r)
    # cprint(p)
    # yprint(example)
