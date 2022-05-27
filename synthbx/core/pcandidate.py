from synthbx.ast.program import Program
from synthbx.ast.type import Type, NumberType, SymbolType
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
from synthbx.env.const import ESuffix, EPrefix
from synthbx.util.list import mapin, mapto
from collections import Counter
import itertools
import re


def build_put_cand(dprogram, fexample, schema_partition):

    cprogram = dprogram.clone()
    cprogram.directives = []

    update_rdd_uid(cprogram, schema_partition)

    cprogram.add_rules(
        gen_delta_tlr(dprogram.relation_decls, schema_partition)
    )

    rules = []
    facts = []

    sdt_rules = {arule: None for arule in dprogram.rules}

    for arule in dprogram.rules:
        rs, fs = gen_atomic_tlr(arule, fexample, cprogram.relation_decls)
        rules += rs
        facts += fs
        sdt_rules[arule] = rs

    cprogram.add_rules(rules)
    cprogram.add_facts(facts)

    cprogram.add_rules(
        gen_correlation_tlr(sdt_rules, dprogram)
    )

    fr = handle_fr(cprogram, schema_partition)

    count = mod_for_rule_selection(cprogram)

    return cprogram, count, fr


def update_rdd_uid(cprogram, schema_partition):
    """
    update relation_decl and directives of cprogram
        for *_update, *_(sdt|vdt)_(insert|delete)

    Args:
        cprogram (Program): candidate program
        schema_partition (tuple): schema.partition()
    """

    source, view, _ = schema_partition
    source_names = [s.name for s in source]
    view_names = [v.name for v in view]

    rds = []
    ds = []

    for rd in cprogram.relation_decls:
        rds.append(
            Relation(
                name=rd.name + ESuffix.UPDATE,
                schema=rd.schema
            ).clone()
        )

        if rd.name not in view_names:
            rds.append(
                Relation(
                    name=rd.name + ESuffix.SDT_INSERT,
                    schema=rd.schema
                ).clone()
            )

            rds.append(
                Relation(
                    name=rd.name + ESuffix.SDT_DELETE,
                    schema=rd.schema
                ).clone()
            )

        if rd.name not in source_names:
            rds.append(
                Relation(
                    name=rd.name + ESuffix.VDT_INSERT,
                    schema=rd.schema
                ).clone()
            )

            rds.append(
                Relation(
                    name=rd.name + ESuffix.VDT_DELETE,
                    schema=rd.schema
                ).clone()
            )

    cprogram.add_relation_decls(rds)

    for rd in cprogram.relation_decls:
        ds.append(
            Directive(
                type=DirectiveType.OUTPUT,
                name=rd.name
            )
        )

    for d in ds:
        if d.name in source_names:
            d.type = DirectiveType.INPUT

    for vn in view_names:
        for d in ds:
            if d.name == vn + ESuffix.UPDATE:
                d.type = DirectiveType.INPUT

    cprogram.directives = ds


def make_su_rules(source):
    """
    P[source_update <- (source, source_sdt_(insert|delete))]

    source_update :- source, !source_sdt_delete; source_sdt_insert

    Args:
        source (Relation)

    Returns:
        list<Rule>
    """

    rs = []
    sn = source.name
    args = source.args()

    rs.append(
        Rule(
            head=Atom(
                name=sn + ESuffix.UPDATE,
                args=args
            ),
            body=[
                Conjunction(items=[
                    Atom(
                        name=sn,
                        args=args
                    ),
                    Negation(atom=Atom(
                        name=sn + ESuffix.SDT_DELETE,
                        args=args
                    ))
                ]),
                Conjunction(items=[
                    Atom(
                        name=sn + ESuffix.SDT_INSERT,
                        args=args
                    )
                ])
            ]
        ).clone()
    )

    return rs


def make_vdt_rules(view):
    """
    P[view_vdt_(insert|delete) <- (view, view_update)]

    view_vdt_delete :- view, !view_update
    view_vdt_insert :- view_update, !view

    Args:
        view (Relation)

    Returns:
        list<Rule>
    """

    rs = []
    vn = view.name
    args = view.args()

    rs.append(
        Rule(
            head=Atom(
                name=vn + ESuffix.VDT_DELETE,
                args=args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=vn,
                    args=args
                ),
                Negation(atom=Atom(
                    name=vn + ESuffix.UPDATE,
                    args=args
                ))
            ])]
        ).clone()
    )

    rs.append(
        Rule(
            head=Atom(
                name=vn + ESuffix.VDT_INSERT,
                args=args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=vn + ESuffix.UPDATE,
                    args=args
                ),
                Negation(atom=Atom(
                    name=vn,
                    args=args
                ))
            ])]
        ).clone()
    )
    return rs


def gen_delta_tlr(relation_decls, schema_partition):
    """
    call make_su_rules & make_vdt_rules

    Args:
        relation_decls (list<Relation>): dprogram.relation_decls (without uid)
        schema_partition (tuple): schema.partition()

    Returns:
        list<Rule>
    """

    rs = []

    source, view, _ = schema_partition
    source_names = [s.name for s in source]
    view_names = [v.name for v in view]

    m_sourced = []
    m_viewd = []

    for rd in relation_decls:
        if rd.name not in view_names:
            m_sourced.append(rd)

        if rd.name not in source_names:
            m_viewd.append(rd)

    for s in m_sourced:
        rs += make_su_rules(source=s)

    for v in m_viewd:
        rs += make_vdt_rules(view=v)

    return rs


def gen_atomic_tlr(arule, fexample, relation_decls):
    """
    gen atomic templates

    Args:
        arule (Rule): atomic rule
        fexample (Example): full example
        relation_decls (list<Relation>): cprogram.relation_decls

    Returns:
        list<Rule>, list<Fact>
    """

    func_name = 'build_tlr_' + arule.atype().name[0].lower()

    print('==type = ' + arule.atype().name)

    rs, fs = globals()[func_name](arule, fexample, relation_decls)

    return rs, fs


def build_tlr_r(arule, fexample, relation_decls):
    """_summary_

    Args:
        arule (_type_): _description_
        fexample (_type_): _description_
        relation_decls (_type_): _description_

    Returns:
        list<Rule>, list<Fact>
    """

    rs, fs = [], []

    view = arule.head
    source = arule.body[0].literals()[0]

    rs_d, rs_i = [], []

    rs_d.append(
        Rule(
            head=Atom(
                name=source.name + ESuffix.SDT_DELETE,
                args=source.args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=view.name + ESuffix.VDT_DELETE,
                    args=view.args
                )
            ])]
        ).clone()
    )

    rs_i.append(
        Rule(
            head=Atom(
                name=source.name + ESuffix.SDT_INSERT,
                args=source.args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=view.name + ESuffix.VDT_INSERT,
                    args=view.args
                )
            ])]
        ).clone()
    )

    rs = rs_d + rs_i

    return rs, fs


def build_tlr_u(arule, fexample, relation_decls):
    """_summary_

    Args:
        arule (_type_): _description_
        fexample (_type_): _description_
        relation_decls (_type_): _description_

    Returns:
        list<Rule>, list<Fact>
    """

    rs, fs = [], []

    view = arule.head
    sources = [
        arule.body[0].literals()[0],
        arule.body[1].literals()[0]
    ]

    rs_d, rs_i = [], []

    for source in sources:
        rs_d.append(
            Rule(
                head=Atom(
                    name=source.name + ESuffix.SDT_DELETE,
                    args=source.args
                ),
                body=[Conjunction(items=[
                    Atom(
                        name=view.name + ESuffix.VDT_DELETE,
                        args=view.args
                    ),
                    Atom(
                        name=source.name,
                        args=source.args
                    )
                ])]
            ).clone()
        )

        rs_i.append(
            Rule(
                head=Atom(
                    name=source.name + ESuffix.SDT_INSERT,
                    args=source.args
                ),
                body=[Conjunction(items=[
                    Atom(
                        name=view.name + ESuffix.VDT_INSERT,
                        args=view.args
                    ),
                    Negation(atom=Atom(
                        name=source.name,
                        args=source.args,
                    ))
                ])]
            ).clone()
        )

    t_ins = [[], [], []]

    t_ins[0] = [t.data for t in fexample.tables
                if t.name == view.name and t.is_inserted()][0]
    t_ins[1] = [t.data for t in fexample.tables
                if t.name == sources[0].name and t.is_inserted()][0]
    t_ins[2] = [t.data for t in fexample.tables
                if t.name == sources[1].name and t.is_inserted()][0]

    sap = [
        [row for row in t_ins[0]
         if row in t_ins[1] and row not in t_ins[2]
         ],
        [row for row in t_ins[0]
         if row in t_ins[2] and row not in t_ins[1]
         ],
        [row for row in t_ins[0]
         if row in t_ins[1] and row in t_ins[2]
         ]
    ]

    stat = [len(lst) for lst in sap]

    if stat[0] == 0 and stat[1] == 0 and stat[2] == 0:
        rs = rs_d + rs_i
    elif stat[0] > 0 and stat[1] == 0 and stat[2] == 0:
        rs = rs_d + [rs_i[0]]
    elif stat[0] == 0 and stat[1] > 0 and stat[2] == 0:
        rs = rs_d + [rs_i[1]]
    elif stat[0] == 0 and stat[1] == 0 and stat[2] > 0:
        rs = rs_d + rs_i
    else:
        rs_i = []

        fn = [
            f'{EPrefix.AUX}_U_{view.name}_{sources[0].name}',
            f'{EPrefix.AUX}_U_{view.name}_{sources[1].name}',
            f'{EPrefix.AUX}_U_{view.name}_{sources[0].name}_{sources[1].name}'
        ]

        aux_schema = None
        for rd in relation_decls:
            if rd.name == view.name:
                aux_schema = rd.schema
                break

        for i in [0, 1, 2]:
            if stat[i] > 0:
                relation_decls.append(
                    Relation(
                        name=fn[i],
                        schema=aux_schema
                    ).clone()
                )

                for row in sap[i]:
                    f_args = [Constant(value=f'"{ri}"') for ri in row]
                    fs.append(
                        Fact(atom=Atom(
                            name=fn[i],
                            args=f_args
                        )).clone()
                    )
            else:
                fn[i] = ''

        fn = [f for f in fn if f]

        for source in sources:
            for f in fn:
                rs_i.append(
                    Rule(
                        head=Atom(
                            name=source.name + ESuffix.SDT_INSERT,
                            args=source.args
                        ),
                        body=[Conjunction(items=[
                            Atom(
                                name=view.name + ESuffix.VDT_INSERT,
                                args=view.args
                            ),
                            Atom(
                                name=f,
                                args=view.args
                            ),
                            Negation(atom=Atom(
                                name=source.name,
                                args=source.args,
                            ))
                        ])]
                    ).clone()
                )

                rs_i.append(
                    Rule(
                        head=Atom(
                            name=source.name + ESuffix.SDT_INSERT,
                            args=source.args
                        ),
                        body=[Conjunction(items=[
                            Atom(
                                name=view.name + ESuffix.VDT_INSERT,
                                args=view.args
                            ),
                            Negation(atom=Atom(
                                name=f,
                                args=view.args,
                            )),
                            Negation(atom=Atom(
                                name=source.name,
                                args=source.args,
                            ))
                        ])]
                    ).clone()
                )

        rs = rs_d + rs_i

    return rs, fs


def build_tlr_d(arule, fexample, relation_decls):
    """_summary_

    Args:
        arule (_type_): _description_
        fexample (_type_): _description_
        relation_decls (_type_): _description_

    Returns:
        list<Rule>, list<Fact>
    """

    rs, fs = [], []

    view = arule.head
    sources = arule.body[0].literals()[:2]

    rs_d, rs_i = [], []

    rs_d.append(
        Rule(
            head=Atom(
                name=sources[0].name + ESuffix.SDT_DELETE,
                args=sources[0].args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=view.name + ESuffix.VDT_DELETE,
                    args=view.args
                ),
                Atom(
                    name=sources[0].name,
                    args=sources[0].args,
                )
            ])]
        ).clone()
    )

    rs_d.append(
        Rule(
            head=Atom(
                name=sources[1].name + ESuffix.SDT_DELETE,
                args=sources[1].args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=view.name + ESuffix.VDT_INSERT,
                    args=view.args
                ),
                Atom(
                    name=sources[1].name,
                    args=sources[1].args,
                )
            ])]
        ).clone()
    )

    rs_i.append(
        Rule(
            head=Atom(
                name=sources[0].name + ESuffix.SDT_INSERT,
                args=sources[0].args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=view.name + ESuffix.VDT_INSERT,
                    args=view.args
                ),
                Negation(atom=Atom(
                    name=sources[0].name,
                    args=sources[0].args,
                ))
            ])]
        ).clone()
    )

    rs_i.append(
        Rule(
            head=Atom(
                name=sources[1].name + ESuffix.SDT_INSERT,
                args=sources[1].args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=view.name + ESuffix.VDT_DELETE,
                    args=view.args
                ),
                Negation(atom=Atom(
                    name=sources[1].name,
                    args=sources[1].args,
                ))
            ])]
        ).clone()
    )

    t_del = [[], [], []]
    t_ins = [[], [], []]

    t_del[0] = [t.data for t in fexample.tables
                if t.name == view.name and t.is_deleted()][0]
    t_del[1] = [t.data for t in fexample.tables
                if t.name == sources[0].name and t.is_deleted()][0]
    t_ins[2] = [t.data for t in fexample.tables
                if t.name == sources[1].name and t.is_inserted()][0]

    sap = [
        [row for row in t_del[0]
         if row in t_del[1] and row not in t_ins[2]
         ],
        [row for row in t_del[0]
         if row in t_ins[2] and row not in t_del[1]
         ],
        [row for row in t_del[0]
         if row in t_del[1] and row in t_ins[2]
         ]
    ]

    stat = [len(lst) for lst in sap]

    if stat[0] == 0 and stat[1] == 0 and stat[2] == 0:
        rs = rs_d + [rs_i[0]]
    elif stat[0] > 0 and stat[1] == 0 and stat[2] == 0:
        rs = rs_d + [rs_i[0]]
    elif stat[0] == 0 and stat[1] > 0 and stat[2] == 0:
        rs = [rs_d[1]] + rs_i
    elif stat[0] == 0 and stat[1] == 0 and stat[2] > 0:
        rs = rs_d + rs_i
    else:
        rs_i = [rs_i[0]]
        rs_d = [rs_d[1]]

        fn = [
            f'{EPrefix.AUX}_D_{view.name}_{sources[0].name}',
            f'{EPrefix.AUX}_D_{view.name}_{sources[1].name}',
            f'{EPrefix.AUX}_D_{view.name}_{sources[0].name}_{sources[1].name}'
        ]

        aux_schema = None
        for rd in relation_decls:
            if rd.name == view.name:
                aux_schema = rd.schema
                break

        for i in [0, 1, 2]:
            if stat[i] > 0:
                relation_decls.append(
                    Relation(
                        name=fn[i],
                        schema=aux_schema
                    ).clone()
                )

                for row in sap[i]:
                    f_args = [Constant(value=f'"{ri}"') for ri in row]
                    fs.append(
                        Fact(atom=Atom(
                            name=fn[i],
                            args=f_args
                        )).clone()
                    )
            else:
                fn[i] = ''

        fn = [f for f in fn if f]

        for f in fn:
            rs_d.append(
                Rule(
                    head=Atom(
                        name=sources[0].name + ESuffix.SDT_DELETE,
                        args=sources[0].args
                    ),
                    body=[Conjunction(items=[
                        Atom(
                            name=view.name + ESuffix.VDT_DELETE,
                            args=view.args
                        ),
                        Atom(
                            name=sources[0].name,
                            args=sources[0].args
                        ),
                        Atom(
                            name=f,
                            args=view.args
                        )
                    ])]
                ).clone()
            )

            rs_d.append(
                Rule(
                    head=Atom(
                        name=sources[0].name + ESuffix.SDT_DELETE,
                        args=sources[0].args
                    ),
                    body=[Conjunction(items=[
                        Atom(
                            name=view.name + ESuffix.VDT_DELETE,
                            args=view.args
                        ),
                        Atom(
                            name=sources[0].name,
                            args=sources[0].args
                        ),
                        Negation(atom=Atom(
                            name=f,
                            args=view.args
                        ))
                    ])]
                ).clone()
            )

            rs_i.append(
                Rule(
                    head=Atom(
                        name=sources[1].name + ESuffix.SDT_INSERT,
                        args=sources[1].args
                    ),
                    body=[Conjunction(items=[
                        Atom(
                            name=view.name + ESuffix.VDT_DELETE,
                            args=view.args
                        ),
                        Atom(
                            name=f,
                            args=view.args,
                        ),
                        Negation(atom=Atom(
                            name=sources[1].name,
                            args=sources[1].args
                        ))
                    ])]
                ).clone()
            )

            rs_i.append(
                Rule(
                    head=Atom(
                        name=sources[1].name + ESuffix.SDT_INSERT,
                        args=sources[1].args
                    ),
                    body=[Conjunction(items=[
                        Atom(
                            name=view.name + ESuffix.VDT_DELETE,
                            args=view.args
                        ),
                        Negation(atom=Atom(
                            name=f,
                            args=view.args
                        )),
                        Negation(atom=Atom(
                            name=sources[1].name,
                            args=sources[1].args
                        ))
                    ])]
                ).clone()
            )

        rs = rs_d + rs_i

    return rs, fs


def build_tlr_i(arule, fexample, relation_decls):
    """_summary_

    Args:
        arule (_type_): _description_
        fexample (_type_): _description_
        relation_decls (_type_): _description_

    Returns:
        list<Rule>, list<Fact>
    """

    rs, fs = [], []

    view = arule.head
    sources = arule.body[0].literals()[:2]

    rs_d, rs_i = [], []

    for source in sources:
        rs_d.append(
            Rule(
                head=Atom(
                    name=source.name + ESuffix.SDT_DELETE,
                    args=source.args
                ),
                body=[Conjunction(items=[
                    Atom(
                        name=view.name + ESuffix.VDT_DELETE,
                        args=view.args
                    ),
                    Atom(
                        name=source.name,
                        args=source.args
                    )
                ])]
            ).clone()
        )

        rs_i.append(
            Rule(
                head=Atom(
                    name=source.name + ESuffix.SDT_INSERT,
                    args=source.args
                ),
                body=[Conjunction(items=[
                    Atom(
                        name=view.name + ESuffix.VDT_INSERT,
                        args=view.args
                    ),
                    Negation(atom=Atom(
                        name=source.name,
                        args=source.args
                    ))
                ])]
            ).clone()
        )

    t_del = [[], [], []]

    t_del[0] = [t.data for t in fexample.tables
                if t.name == view.name and t.is_deleted()][0]
    t_del[1] = [t.data for t in fexample.tables
                if t.name == sources[0].name and t.is_deleted()][0]
    t_del[2] = [t.data for t in fexample.tables
                if t.name == sources[1].name and t.is_deleted()][0]

    sap = [
        [row for row in t_del[0]
         if row in t_del[1] and row not in t_del[2]
         ],
        [row for row in t_del[0]
         if row in t_del[2] and row not in t_del[1]
         ],
        [row for row in t_del[0]
         if row in t_del[1] and row in t_del[2]
         ]
    ]

    stat = [len(lst) for lst in sap]

    if stat[0] == 0 and stat[1] == 0 and stat[2] == 0:
        rs = rs_d + rs_i
    elif stat[0] > 0 and stat[1] == 0 and stat[2] == 0:
        rs = [rs_d[0]] + rs_i
    elif stat[0] == 0 and stat[1] > 0 and stat[2] == 0:
        rs = [rs_d[1]] + rs_i
    elif stat[0] == 0 and stat[1] == 0 and stat[2] > 0:
        rs = rs_d + rs_i
    else:
        rs_d = []

        fn = [
            f'{EPrefix.AUX}_I_{view.name}_{sources[0].name}',
            f'{EPrefix.AUX}_I_{view.name}_{sources[1].name}',
            f'{EPrefix.AUX}_I_{view.name}_{sources[0].name}_{sources[1].name}'
        ]

        aux_schema = None
        for rd in relation_decls:
            if rd.name == view.name:
                aux_schema = rd.schema
                break

        for i in [0, 1, 2]:
            if stat[i] > 0:
                relation_decls.append(
                    Relation(
                        name=fn[i],
                        schema=aux_schema
                    ).clone()
                )

                for row in sap[i]:
                    f_args = [Constant(value=f'"{ri}"') for ri in row]
                    fs.append(
                        Fact(atom=Atom(
                            name=fn[i],
                            args=f_args
                        )).clone()
                    )
            else:
                fn[i] = ''

        fn = [f for f in fn if f]

        for source in sources:
            for f in fn:
                rs_d.append(
                    Rule(
                        head=Atom(
                            name=source.name + ESuffix.SDT_DELETE,
                            args=source.args
                        ),
                        body=[Conjunction(items=[
                            Atom(
                                name=view.name + ESuffix.VDT_DELETE,
                                args=view.args
                            ),
                            Atom(
                                name=source.name,
                                args=source.args,
                            ),
                            Atom(
                                name=f,
                                args=view.args
                            ),
                        ])]
                    ).clone()
                )

                rs_d.append(
                    Rule(
                        head=Atom(
                            name=source.name + ESuffix.SDT_DELETE,
                            args=source.args
                        ),
                        body=[Conjunction(items=[
                            Atom(
                                name=view.name + ESuffix.VDT_DELETE,
                                args=view.args
                            ),
                            Atom(
                                name=source.name,
                                args=source.args,
                            ),
                            Negation(atom=Atom(
                                name=f,
                                args=view.args
                            ))
                        ])]
                    ).clone()
                )

        rs = rs_d + rs_i

    return rs, fs


def build_tlr_s(arule, fexample, relation_decls):
    """_summary_

    Args:
        arule (_type_): _description_
        fexample (_type_): _description_
        relation_decls (_type_): _description_

    Returns:
        list<Rule>, list<Fact>
    """

    rs, fs = [], []

    view = arule.head
    source = arule.body[0].literals()[0]
    constraint = arule.body[0].constraints()

    rs_d, rs_i = [], []
    rs_fg = []

    rs_d.append(
        Rule(
            head=Atom(
                name=source.name + ESuffix.SDT_DELETE,
                args=source.args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=view.name + ESuffix.VDT_DELETE,
                    args=view.args
                ),
                Atom(
                    name=source.name,
                    args=source.args
                )
            ])]
        ).clone()
    )

    rs_i.append(
        Rule(
            head=Atom(
                name=source.name + ESuffix.SDT_INSERT,
                args=source.args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=view.name + ESuffix.VDT_INSERT,
                    args=view.args
                ),
                Negation(atom=Atom(
                    name=source.name,
                    args=source.args
                ))
            ])]
        ).clone()
    )

    for cs in constraint:
        for state in ['', ESuffix.UPDATE]:
            rs_fg.append(
                Rule(
                    head=RejectAtom(),
                    body=[Conjunction(items=[
                        Atom(
                            name=view.name + state,
                            args=args_cwa(view, cs)
                        ),
                        Constraint(
                            cmp=Cmp.negate(cs.cmp),
                            var=cs.var,
                            const=cs.const
                        )
                    ])]
                ).clone()
            )

    rs = rs_d + rs_i + rs_fg

    return rs, fs


def build_tlr_p(arule, fexample, relation_decls):
    rs, fs = [], []

    view = arule.head
    source = arule.body[0].literals()[0]

    rs_d, rs_i = [], []

    rs_d.append(
        Rule(
            head=Atom(
                name=source.name + ESuffix.SDT_DELETE,
                args=source.args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=view.name + ESuffix.VDT_DELETE,
                    args=view.args
                ),
                Atom(
                    name=source.name,
                    args=source.args
                )
            ])]
        ).clone()
    )

    t_ins = [[]]

    t_ins[0] = [t.data for t in fexample.tables
                if t.name == source.name and t.is_inserted()][0]

    fn = [
        f'{EPrefix.AUX}_P_0_{view.name}_{source.name}',
        f'{EPrefix.AUX}_P_1_{view.name}_{source.name}'
    ]

    s_schema = None
    for rd in relation_decls:
        if rd.name == source.name:
            s_schema = rd.schema
            break

    index_args_d = [source.args.index(a) for a in args_d(source, view)]
    aux_schema = [s_schema[i] for i in index_args_d]

    relation_decls.append(
        Relation(
            name=fn[0],
            schema=aux_schema
        ).clone()
    )

    if len(t_ins[0]) < 2:
        f_args = None
        if not t_ins[0]:
            f_args = [NullConstant() for i in range(len(aux_schema))]
        else:
            row = t_ins[0][0]
            f_args = [Constant(value=f'"{row[i]}"') for i in index_args_d]

        fs.append(
            Fact(atom=Atom(
                name=fn[0],
                args=f_args
            )).clone()
        )

        rs_i.append(
            Rule(
                head=Atom(
                    name=source.name + ESuffix.SDT_INSERT,
                    args=source.args
                ),
                body=[Conjunction(items=[
                    Atom(
                        name=view.name + ESuffix.VDT_INSERT,
                        args=view.args
                    ),
                    Atom(
                        name=fn[0],
                        args=args_d(source, view)
                    ),
                    Negation(atom=Atom(
                        name=source.name,
                        args=args_wa(source, view)
                    ))
                ])]
            ).clone()
        )
    else:
        relation_decls.append(
            Relation(
                name=fn[1],
                schema=s_schema
            ).clone()
        )

        proj_row = []
        for row in t_ins[0]:
            proj_row.append(
                tuple([row[i] for i in index_args_d])
            )

        mcm_proj_row = list(Counter(proj_row).most_common()[0][0])
        rem_row = [row for row in t_ins[0]
                   if [row[i] for i in index_args_d] != mcm_proj_row
                   ]

        f_args = [Constant(value=f'"{ri}"') for ri in mcm_proj_row]
        fs.append(
            Fact(atom=Atom(
                name=fn[0],
                args=f_args
            )).clone()
        )

        for row in rem_row:
            f_args = [Constant(value=f'"{ri}"') for ri in row]
            fs.append(
                Fact(atom=Atom(
                    name=fn[1],
                    args=f_args
                )).clone()
            )

        rs_i.append(
            Rule(
                head=Atom(
                    name=source.name + ESuffix.SDT_INSERT,
                    args=source.args
                ),
                body=[Conjunction(items=[
                    Atom(
                        name=view.name + ESuffix.VDT_INSERT,
                        args=view.args
                    ),
                    Atom(
                        name=fn[1],
                        args=source.args
                    ),
                    Negation(atom=Atom(
                        name=source.name,
                        args=args_wa(source, view)
                    ))
                ])]
            ).clone()
        )

        rs_i.append(
            Rule(
                head=Atom(
                    name=source.name + ESuffix.SDT_INSERT,
                    args=source.args
                ),
                body=[Conjunction(items=[
                    Atom(
                        name=view.name + ESuffix.VDT_INSERT,
                        args=view.args
                    ),
                    Atom(
                        name=fn[0],
                        args=args_d(source, view)
                    ),
                    Negation(atom=Atom(
                        name=fn[1],
                        args=args_wa(source, view)
                    )),
                    Negation(atom=Atom(
                        name=source.name,
                        args=args_wa(source, view)
                    ))
                ])]
            ).clone()
        )

    rs = rs_d + rs_i

    return rs, fs


def build_tlr_j(arule, fexample, relation_decls):
    """_summary_

    Args:
        arule (_type_): _description_
        fexample (_type_): _description_
        relation_decls (_type_): _description_

    Returns:
        list<Rule>, list<Fact>
    """

    rs, fs = [], []

    view = arule.head
    sources = arule.body[0].literals()[:2]

    rs_d, rs_i = [], []
    rs_fg = []

    for source in sources:
        rs_d.append(
            Rule(
                head=Atom(
                    name=source.name + ESuffix.SDT_DELETE,
                    args=source.args
                ),
                body=[Conjunction(items=[
                    Atom(
                        name=view.name + ESuffix.VDT_DELETE,
                        args=args_wa(view, source)
                    ),
                    Atom(
                        name=source.name,
                        args=source.args
                    )
                ])]
            ).clone()
        )

        rs_i.append(
            Rule(
                head=Atom(
                    name=source.name + ESuffix.SDT_INSERT,
                    args=source.args
                ),
                body=[Conjunction(items=[
                    Atom(
                        name=view.name + ESuffix.VDT_INSERT,
                        args=args_wa(view, source)
                    ),
                    Negation(atom=Atom(
                        name=source.name,
                        args=source.args
                    ))
                ])]
            ).clone()
        )

    if set(sources[0].args) == set(view.args) \
            and set(sources[1].args) == set(view.args):
        pass
    else:
        for i, source in enumerate(sources):
            rs_fg.append(
                Rule(
                    head=RejectAtom(),
                    body=[Conjunction(items=[
                        Atom(
                            name=source.name + ESuffix.SDT_INSERT,
                            args=args_jwa(source, sources[1-i])
                        ),
                        Atom(
                            name=source.name,
                            args=args_jwa(source, sources[1-i])
                        )])
                    ]
                ).clone()
            )

        rs_fg.append(
            Rule(
                head=RejectAtom(),
                body=[Conjunction(items=[
                    Atom(
                        name=sources[0].name + ESuffix.SDT_DELETE,
                        args=args_jwa(sources[0], sources[1])
                    ),
                    Atom(
                        name=sources[0].name + ESuffix.UPDATE,
                        args=args_jwa(sources[0], sources[1])
                    ),
                    Atom(
                        name=sources[1].name + ESuffix.SDT_DELETE,
                        args=args_jwa(sources[1], sources[0])
                    ),
                    Atom(
                        name=sources[1].name + ESuffix.UPDATE,
                        args=args_jwa(sources[1], sources[0])
                    ),
                ])]
            ).clone()
        )
        pass

    rs += rs_fg

    map0 = mapin(sources[0].args, view.args)
    map1 = mapin(sources[1].args, view.args)

    t_del = [[], [], []]

    t_del[0] = [t.data for t in fexample.tables
                if t.name == view.name and t.is_deleted()][0]
    t_del[1] = [t.data for t in fexample.tables
                if t.name == sources[0].name and t.is_deleted()][0]
    t_del[2] = [t.data for t in fexample.tables
                if t.name == sources[1].name and t.is_deleted()][0]

    sap = [
        [row for row in t_del[0]
         if mapto(row, map0) in t_del[1] and
            mapto(row, map1) not in t_del[2]
         ],
        [row for row in t_del[0]
         if mapto(row, map1) in t_del[2] and
            mapto(row, map0) not in t_del[1]
         ],
        [row for row in t_del[0]
         if mapto(row, map0) in t_del[1] and
            mapto(row, map1) in t_del[2]
         ]
    ]

    stat = [len(lst) for lst in sap]

    if stat[0] == 0 and stat[1] == 0 and stat[2] == 0:
        rs += [rs_d[0]] + rs_i
    elif stat[0] > 0 and stat[1] == 0 and stat[2] == 0:
        rs += [rs_d[0]] + rs_i
    elif stat[0] == 0 and stat[1] > 0 and stat[2] == 0:
        rs += [rs_d[1]] + rs_i
    elif stat[0] == 0 and stat[1] == 0 and stat[2] > 0:
        rs += rs_d + rs_i
    else:
        rs_d = []

        fn = [
            f'{EPrefix.AUX}_J_{view.name}_{sources[0].name}',
            f'{EPrefix.AUX}_J_{view.name}_{sources[1].name}',
            f'{EPrefix.AUX}_J_{view.name}_{sources[0].name}_{sources[1].name}'
        ]

        aux_schema = None
        for rd in relation_decls:
            if rd.name == view.name:
                aux_schema = rd.schema
                break

        for i in [0, 1, 2]:
            if stat[i] > 0:
                relation_decls.append(
                    Relation(
                        name=fn[i],
                        schema=aux_schema
                    ).clone()
                )

                for row in sap[i]:
                    f_args = [Constant(value=f'"{ri}"') for ri in row]
                    fs.append(
                        Fact(atom=Atom(
                            name=fn[i],
                            args=f_args
                        )).clone()
                    )
            else:
                fn[i] = ''

        fn = [f for f in fn if f]

        for source in sources:
            for f in fn:
                rs_d.append(
                    Rule(
                        head=Atom(
                            name=source.name + ESuffix.SDT_DELETE,
                            args=source.args
                        ),
                        body=[Conjunction(items=[
                            Atom(
                                name=view.name + ESuffix.VDT_DELETE,
                                args=args_wa(view, source)
                            ),
                            Atom(
                                name=source.name,
                                args=source.args,
                            ),
                            Atom(
                                name=f,
                                args=args_wa(view, source)
                            ),
                        ])]
                    ).clone()
                )

                rs_d.append(
                    Rule(
                        head=Atom(
                            name=source.name + ESuffix.SDT_DELETE,
                            args=source.args
                        ),
                        body=[Conjunction(items=[
                            Atom(
                                name=view.name + ESuffix.VDT_DELETE,
                                args=args_wa(view, source)
                            ),
                            Atom(
                                name=source.name,
                                args=source.args,
                            ),
                            Negation(atom=Atom(
                                name=f,
                                args=args_wa(view, source)
                            ))
                        ])]
                    ).clone()
                )

        rs += rs_d + rs_i

    return rs, fs


def build_tlr_c(arule, fexample, relation_decls):
    """_summary_

    Args:
        arule (_type_): _description_
        fexample (_type_): _description_
        relation_decls (_type_): _description_

    Returns:
        list<Rule>, list<Fact>
    """

    rs, fs = [], []

    view = arule.head
    source = arule.body[0].literals()[0]
    constraint = arule.body[0].constraints()

    rs_d, rs_i = [], []
    rs_fg = []

    rs_d.append(
        Rule(
            head=Atom(
                name=source.name + ESuffix.SDT_DELETE,
                args=source.args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=view.name + ESuffix.VDT_DELETE,
                    args=args_wa(view, source)
                ),
                Atom(
                    name=source.name,
                    args=source.args
                )
            ])]
        ).clone()
    )

    rs_i.append(
        Rule(
            head=Atom(
                name=source.name + ESuffix.SDT_INSERT,
                args=source.args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=view.name + ESuffix.VDT_INSERT,
                    args=args_wa(view, source)
                ),
                Negation(atom=Atom(
                    name=source.name,
                    args=source.args
                ))
            ])]
        ).clone()
    )

    for cs in constraint:
        for state in ['', ESuffix.UPDATE]:
            rs_fg.append(
                Rule(
                    head=RejectAtom(),
                    body=[Conjunction(items=[
                        Atom(
                            name=view.name + state,
                            args=args_cwa(view, cs)
                        ),
                        Constraint(
                            cmp=Cmp.negate(cs.cmp),
                            var=cs.var,
                            const=cs.const
                        )
                    ])]
                ).clone()
            )

    rs = rs_d + rs_i + rs_fg

    return rs, fs


def gen_correlation_tlr(sdt_rules, dprogram):
    rs = []

    rds_names = {rd.name for rd in dprogram.relation_decls}
    g_dict = {name: [] for name in rds_names}

    for r in dprogram.rules:
        if r.is_id_rule() or r.is_s_rule() or r.is_p_rule():
            g_dict[r.body[0].items[0].name].append(r)

    for k in g_dict:
        if len(g_dict[k]) == 1:
            continue

        rd_k = [rd for rd in dprogram.relation_decls if rd.name == k][0]

        for rc in itertools.combinations(g_dict[k], 2):
            for i in [0, 1]:
                rs += adapt_tlr(
                    sdt_rules[rc[i]], rd_k, rc[i].head, rc[1-i].head
                )

    for r in dprogram.rules:
        if r.is_d_rule() \
                and re.match(r'.*_\d+' + re.escape(ESuffix.ALIAS), r.body[0].items[0].name):

            sources = [r.body[0].items[0], r.body[0].items[1]]
            view = r.head

            rs.append(
                Rule(
                    head=Atom(
                        name=sources[1].name + ESuffix.SDT_INSERT,
                        args=sources[1].args
                    ),
                    body=[Conjunction(items=[
                        Atom(
                            name=sources[0].name + ESuffix.SDT_INSERT,
                            args=sources[0].args
                        ),
                        Negation(atom=Atom(
                            name=sources[1].name,
                            args=sources[1].args,
                        )),
                        Negation(atom=Atom(
                            name=view.name + ESuffix.VDT_INSERT,
                            args=view.args,
                        ))
                    ])]
                ).clone()
            )

            # rs.append(
            #     Rule(
            #         head=Atom(
            #             name=sources[1].name + ESuffix.SDT_DELETE,
            #             args=sources[1].args
            #         ),
            #         body=[Conjunction(items=[
            #             Atom(
            #                 name=sources[0].name + ESuffix.SDT_DELETE,
            #                 args=sources[0].args
            #             ),
            #             Atom(
            #                 name=sources[1].name,
            #                 args=sources[1].args,
            #             ),
            #             Negation(atom=Atom(
            #                 name=view.name + ESuffix.SDT_DELETE,
            #                 args=view.args,
            #             ))
            #         ])]
            #     ).clone()
            # )

    return rs


def adapt_tlr(sdt_rules, rd_s, l_v0, l_v1):
    rs = []

    args_s_wa = [a if a in l_v0.args or a in l_v1.args
                 else AnonymousVariable()
                 for a in rd_s.args()]

    sdt_d_rules, sdt_i_rules = [], []
    for r in sdt_rules:
        if r.head.name.endswith(ESuffix.SDT_DELETE):
            sdt_d_rules.append(r)
        else:
            sdt_i_rules.append(r)

    # there is only 1 sdt_d_rule for R_RULE, P_RULE, S_RULE
    # but there are possibly more than 1 sdt_i_rule because of aux literals

    rs.append(
        Rule(
            head=Atom(
                name=l_v1.name + ESuffix.SDT_DELETE,
                args=l_v1.args
            ),
            body=[Conjunction(items=[
                Atom(
                    name=l_v0.name + ESuffix.SDT_DELETE,
                    args=l_v0.args
                ),
                Atom(
                    name=rd_s.name,
                    args=args_s_wa
                )
            ])]
        ).clone()
    )

    for r in sdt_i_rules:
        aux = []
        for l in r.literals():
            if l.name.startswith(EPrefix.AUX):
                aux.append(l)

        rs.append(
            Rule(
                head=Atom(
                    name=l_v1.name + ESuffix.SDT_INSERT,
                    args=l_v1.args
                ),
                body=[Conjunction(items=[
                    Atom(
                        name=l_v0.name + ESuffix.SDT_INSERT,
                        args=l_v0.args
                    )
                ] + aux + [
                    Negation(atom=Atom(
                        name=rd_s.name,
                        args=args_s_wa
                    ))
                ])]
            ).clone()
        )

    return rs


def handle_fr(cprogram, schema_partition):

    fr = False

    for r in cprogram.rules:
        if r.is_flag_rule():
            fr = True
            break

    if not fr:
        return False

    cprogram.add_relation_decl(RejectRelation())

    cprogram.add_directive(
        Directive(
            type=DirectiveType.OUTPUT,
            name=EPrefix.FLAG_R
        ).clone()
    )

    # for switching to Fv()
    cprogram.add_relation_decl(ValidRelation())

    cprogram.add_directive(
        Directive(
            type=DirectiveType.OUTPUT,
            name=EPrefix.FLAG_V,
        ).clone()
    )

    cprogram.add_rule(
        Rule(
            head=ValidAtom(),
            body=[Conjunction(items=[
                # Negation(atom=Atom(
                #     name=EPrefix.FLAG_R,
                #     args=[AnonymousVariable()]
                # ))
                Negation(atom=RejectAtom())
            ])]
        ).clone()
    )

    return True


def mod_for_rule_selection(cprogram):
    """
    add .decl Rule(v0: number)
    add .input Rule
    add literal Rule(xxx) in the end of source_sdt_(insert|delete)
    """
    cprogram.add_relation_decl(
        Relation(
            name='Rule',
            schema=[NumberType()]
        ).clone()
    )

    cprogram.add_directive(
        Directive(
            type=DirectiveType.INPUT,
            name='Rule',
        ).clone()
    )

    count = -1
    for r in cprogram.rules:
        if r.head.name.endswith(tuple([ESuffix.SDT_INSERT, ESuffix.SDT_DELETE])):
            # c_flag = False
            # for l in r.body_literals():
            #     if l.name.endswith(tuple([ESuffix.SDT_INSERT, ESuffix.SDT_DELETE])):
            #         c_flag = True

            # if c_flag:
            #     continue

            count += 1
            r.body[0].items.append(
                Atom(
                    name='Rule',
                    args=[Constant(value=count)]
                ).clone()
            )

    return count + 1


def args_wa(l, lx):
    """_summary_

    Args:
        l (Atom): _description_
        lx (Atom): _description_

    Returns:
        list<Variable>
    """
    return [a if a in lx.args else AnonymousVariable() for a in l.args]


def args_cwa(l, c):
    """_summary_

    Args:
        l (Atom): _description_
        c (list<Constraint>): _description_

    Returns:
        list<Variable>
    """
    return [a if a == c.var else AnonymousVariable() for a in l.args]


def args_jwa(l, lx):
    """_summary_

    Args:
        l (Atom): _description_
        lx (Atom): _description_

    Returns:
        list<Variable>
    """
    args_j = set(l.args).intersection(set(lx.args))
    return [a if a in args_j else AnonymousVariable() for a in l.args]


def args_oa(l):
    """_summary_

    Args:
        l (Atom): _description_

    Returns:
        list<Variable>
    """
    return [AnonymousVariable() for i in range(len(l.args))]


def args_d(l, lx):
    """_summary_

    Args:
        l (Atom): _description_
        lx (Atom): _description_

    Returns:
        list<Variable>
    """
    return [a for a in l.args if a not in lx.args]


if __name__ == '__main__':
    pass
