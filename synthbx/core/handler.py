from synthbx.ast.relation import Relation
from synthbx.ast.directive import Directive, DirectiveType
from synthbx.ast.rule import Rule
from synthbx.ast.conjunction import Conjunction
from synthbx.ast.atom import Atom, RejectAtom, ValidAtom
from synthbx.ast.negation import Negation
from synthbx.env.const import ESuffix, EPrefix


def make_valid(pprogram, schema_partition):
    fr = False
    for r in pprogram.rules:
        if r.is_flag_rule():
            fr = True
            break

    if not fr:
        return

    source, _, _ = schema_partition
    s_names = [s.name for s in source]
    su_names = [s + ESuffix.UPDATE for s in s_names]

    for r in pprogram.rules:
        if r.head.name in su_names:
            r.head.name = r.head.name[:-len(ESuffix.UPDATE)] \
                + ESuffix.EVL_UPDATE
        elif r.is_flag_rule():
            for conj in r.body:
                for item in conj.items:
                    if type(item) is Atom and item.name in su_names:
                        item.name = item.name[:-len(ESuffix.UPDATE)] \
                            + ESuffix.EVL_UPDATE

    for rd in pprogram.relation_decls:
        if rd.name in s_names:
            s_args = rd.args()

            pprogram.add_relation_decl(
                Relation(
                    name=rd.name + ESuffix.EVL_UPDATE,
                    schema=rd.schema
                ).clone()
            )

            pprogram.add_directive(
                Directive(
                    type=DirectiveType.OUTPUT,
                    name=rd.name + ESuffix.EVL_UPDATE
                ).clone()
            )

            pprogram.add_rule(
                Rule(
                    head=Atom(
                        name=rd.name + ESuffix.UPDATE,
                        args=s_args
                    ),
                    body=[
                        Conjunction(items=[
                            Atom(
                                name=rd.name + ESuffix.EVL_UPDATE,
                                args=s_args
                            ),
                            ValidAtom()
                        ]),
                        Conjunction(items=[
                            Atom(
                                name=rd.name,
                                args=s_args
                            ),
                            RejectAtom()
                        ])
                    ]
                ).clone()
            )


def clean_p_directives(pprogram, schema_partition):
    source, view, _ = schema_partition

    input_names = [s.name for s in source] + \
        [v.name + ESuffix.UPDATE for v in view]
    output_names = [s.name + ESuffix.UPDATE for s in source]

    ds = [d for d in pprogram.directives
          if d.name not in input_names + output_names +
          [EPrefix.FLAG_V, EPrefix.FLAG_R]
          ]

    [pprogram.directives.remove(d) for d in ds]


def clean_g_directives(gprogram, schema_partition):
    source, view, _ = schema_partition

    input_names = [s.name for s in source]
    output_names = [v.name for v in view]

    ds = [d for d in gprogram.directives
          if d.name not in input_names + output_names
          ]

    [gprogram.directives.remove(d) for d in ds]


def clean_relation_rule(program):
    program.clean_relation(name='Rule')
    for rule in program.rules:
        for conj in rule.body:
            pl_list, nl_list, cs_list = conj.partition()
            pl_list = [l for l in pl_list if l.name != 'Rule']
            conj.items = pl_list + nl_list + cs_list


def clean_unused_units(program):
    fact_names = [fact.atom.name for fact in program.facts]
    used_names = {fact_name: False for fact_name in fact_names}

    for rule in program.rules:
        for conj in rule.body:
            for item in conj.items:
                if type(item) is Atom \
                    and item.name in fact_names \
                        and used_names[item.name] == False:
                    used_names[item.name] = True
                    break
                elif type(item) is Negation \
                        and item.atom.name in fact_names \
                        and used_names[item.name] == False:
                    used_names[item.name] = True
                    break

    unused_names = [f for f in fact_names if not used_names[f]]

    program.clean_relation(unused_names)


if __name__ == '__main__':
    pass
