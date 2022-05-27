from synthbx.ast.schema import Schema
from synthbx.ast.program import Program
from synthbx.ast.unit import Unit
from synthbx.ast.type import Type, SubType, EquiType, SymbolType, NumberType
from synthbx.ast.relation import Relation
from synthbx.ast.directive import Directive, DirectiveType
from synthbx.ast.rule import Rule
from synthbx.ast.atom import Atom
from synthbx.ast.negation import Negation
from synthbx.ast.constraint import Constraint
from synthbx.ast.conjunction import Conjunction
from synthbx.ast.variable import Variable
from synthbx.ast.constant import NumberConstant, SymbolConstant
from synthbx.ast.cmp import Cmp
from synthbx.ast.fact import Fact
from synthbx.util.list import flatten


def make_schema(relation_list):
    return Schema(relations=relation_list)


def make_program(unit_list):
    unit_list = list(flatten(unit_list))
    type_decl_list = [u for u in unit_list if isinstance(u, Type)]
    relation_decl_list = [u for u in unit_list if type(u) is Relation]
    directive_list = [u for u in unit_list if type(u) is Directive]
    rule_list = [u for u in unit_list if type(u) is Rule]
    fact_list = [u for u in unit_list if type(u) is Fact]

    return Program(
        type_decls=type_decl_list,
        relation_decls=relation_decl_list,
        directives=directive_list,
        rules=rule_list,
        facts=fact_list
    )


def make_type(type_name):
    if type_name == 'symbol':
        return SymbolType()
    elif type_name == 'number':
        return NumberType()
    else:
        return make_subtype(type_name, 'symbol')


def make_subtype(ident, type_name):
    return SubType(name=ident, base=Type(type_name))


def make_equitype(ident, type_name):
    return EquiType(name=ident, alias=Type(type_name))


def make_relation(ident, attribute_decl_list):
    return Relation(name=ident, schema=attribute_decl_list)


def make_directive(io, ident_list):
    return [Directive(type=DirectiveType(io), name=ident) for ident in ident_list]


def make_conjunction(items):
    return Conjunction(items=items)


def make_rule(head, body):
    return Rule(head=head, body=body)


def make_fact(atom):
    return Fact(atom=atom)


def make_atom(ident, argument_list):
    return Atom(name=ident, args=argument_list)


def make_negation(atom):
    return Negation(atom=atom)


def make_constraint(variable, cmp, constant):
    return Constraint(cmp=cmp, var=variable, const=constant)


def make_variable(variable):
    return Variable(name=variable)


def make_constant(constant):
    if type(constant) is int:
        return NumberConstant(value=constant)
    elif type(constant) is str:
        return SymbolConstant(value=constant)
    else:
        raise NotImplementedError('Only number and symbol are implemented')
