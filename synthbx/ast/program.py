from synthbx.ast.unit import Unit
from synthbx.env.const import ESuffix, EPrefix


class Program(Unit):
    def __init__(self, type_decls, relation_decls, directives, rules, facts=None):
        self.type_decls = [] if type_decls is None else type_decls
        self.relation_decls = [] if relation_decls is None else relation_decls
        self.directives = [] if directives is None else directives
        self.rules = [] if rules is None else rules
        self.facts = [] if facts is None else facts

        # self.transform()

    def __str__(self):
        vspace = '\n\n'

        type_decls_str = '\n'.join([td.str_of_decl()
                                   for td in self.type_decls])
        relation_decls_str = '\n'.join([rd.str_of_decl()
                                        for rd in self.relation_decls])
        directives_str = '\n'.join([str(d) for d in self.directives])

        rules_update = [r for r in self.rules
                        if r.head.name.endswith(ESuffix.UPDATE)
                        ]
        rules_vdt = [r for r in self.rules
                     if r.head.name.endswith(ESuffix.VDT_INSERT)
                     or r.head.name.endswith(ESuffix.VDT_DELETE)
                     ]
        rules_sdt = [r for r in self.rules
                     if r.head.name.endswith(ESuffix.SDT_INSERT)
                     or r.head.name.endswith(ESuffix.SDT_DELETE)
                     ]
        rules_flag = [r for r in self.rules
                      if r.head.name in [EPrefix.FLAG_R, EPrefix.FLAG_V]
                      ]
        rules_ord = [r for r in self.rules
                     if r not in rules_update + rules_vdt + rules_sdt + rules_flag
                     ]

        rules_update_str = '\n'.join(sorted([str(r) for r in rules_update]))
        rules_vdt_str = '\n'.join(sorted([str(r) for r in rules_vdt]))
        rules_sdt_str = '\n'.join(sorted([str(r) for r in rules_sdt]))
        rules_flag_str = '\n'.join(sorted([str(r) for r in rules_flag]))
        rules_ord_str = '\n'.join(sorted([str(r) for r in rules_ord]))

        facts_str = '\n'.join([str(r) for r in self.facts])
        out = vspace.join(
            list(
                filter(lambda x: x != '',
                       [type_decls_str,
                        relation_decls_str,
                        directives_str,
                        rules_ord_str,
                        rules_vdt_str,
                        rules_update_str,
                        rules_flag_str,
                        rules_sdt_str,
                        facts_str]
                       )
            )
        )
        return out

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    # (add|remove)_type_decl(s)
    def add_type_decl(self, type_decl):
        if type_decl not in self.type_decls:
            self.type_decls.append(type_decl)

    def add_type_decls(self, type_decls):
        [self.add_type_decl(td) for td in type_decls]

    def remove_type_decl(self, type_decl):
        if type_decl in self.type_decls:
            self.type_decls.remove(type_decl)

    def remove_type_decls(self, type_decls):
        [self.remove_type_decl(td) for td in type_decls]

    # (add|remove)_relation_decl(s)
    def add_relation_decl(self, relation_decl):
        if relation_decl not in self.relation_decls:
            self.relation_decls.append(relation_decl)

    def add_relation_decls(self, relation_decls):
        [self.add_relation_decl(rd) for rd in relation_decls]

    def remove_relation_decl(self, relation_decl):
        if relation_decl in self.relation_decls:
            self.relation_decls.remove(relation_decl)

    def remove_relation_decls(self, relation_decls):
        [self.remove_relation_decl(rd) for rd in relation_decls]

    # (add|remove)_directive(s)
    def add_directive(self, directive):
        if directive not in self.directives:
            self.directives.append(directive)

    def add_directives(self, directives):
        [self.add_directive(d) for d in directives]

    def remove_directive(self, directive):
        if directive in self.directives:
            self.directives.remove(directive)

    def remove_directives(self, directives):
        [self.remove_directive(d) for d in directives]

    # (add|remove)_rule(s)
    def add_rule(self, rule):
        if rule not in self.rules:
            self.rules.append(rule)

    def add_rules(self, rules):
        [self.add_rule(r) for r in rules]

    def remove_rule(self, rule):
        if rule in self.rules:
            self.rules.remove(rule)

    def remove_rules(self, rules):
        [self.remove_rule(r) for r in rules]

    # (add|remove)_fact(s)
    def add_fact(self, fact):
        if fact not in self.facts:
            self.facts.append(fact)

    def add_facts(self, facts):
        [self.add_fact(f) for f in facts]

    def remove_fact(self, fact):
        if fact in self.facts:
            self.facts.remove(fact)

    def remove_facts(self, facts):
        [self.remove_fact(f) for f in facts]

    # clean relation(s) and associated type_decl(s), directive(s), fact(s) by relation name(s)
    def clean_relation(self, name):
        rdc = []
        types_c, types_r = set(), set()

        for rd in self.relation_decls:
            if rd.name == name:
                rdc.append(rd)
                types_c |= set(rd.schema)
            else:
                types_r |= set(rd.schema)

        if not rdc:
            return

        self.remove_type_decls([td for td in types_c if td not in types_r])
        self.remove_directives([d for d in self.directives if d.name == name])
        self.remove_facts([f for f in self.facts if f.atom.name == name])
        self.remove_relation_decls(rdc)

    def clean_relations(self, names):
        [self.clean_relation(n) for n in names]

    def transform(self):
        """
        1. Remove duplicates: convert list -> set -> list (don't care about orders)
        2. Assign self.directives to relation_decl.directives in self.relation_decls
        -- Ignore other semantic checking since this self program is checked by Souffe
        """

        self.type_decls = list(set(self.type_decls))
        self.relation_decls = list(set(self.relation_decls))
        self.directives = list(set(self.directives))
        self.rules = list(set(self.rules))
        self.facts = list(set(self.facts))

        for rd in self.relation_decls:
            for d in self.directives:
                if rd.name == d.name:
                    rd.add_directive(d.type)
