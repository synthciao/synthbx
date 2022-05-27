import ply.yacc as yacc
import re
from synthbx.parser.program.lexer import tokens, lex, t_SUBTYPE
import synthbx.parser.maker as maker


def p_program(p):
    '''program : unit_list'''
    p[0] = maker.make_program(p[1])


def p_unit_list(p):
    '''unit_list : unit
            | unit unit_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]


def p_unit(p):
    '''unit : type_decl
            | relation_decl
            | directive
            | rule
            | fact'''
    p[0] = p[1]


def p_type_decl(p):
    '''type_decl : TYPE IDENT
            | TYPE IDENT SUBTYPE type_name
            | TYPE IDENT EQ type_name'''
    if len(p) == 3:
        p[0] = maker.make_subtype(ident=p[2], type_name='symbol')
    elif re.match(t_SUBTYPE, p[3]):
        p[0] = maker.make_subtype(ident=p[2], type_name=p[4])
    else:
        p[0] = maker.make_equitype(ident=p[2], type_name=p[4])


def p_relation_decl(p):
    '''relation_decl : DECL IDENT LPAREN attribute_decl_list RPAREN
        | DECL IDENT LPAREN RPAREN'''
    if len(p) == 6:
        p[0] = maker.make_relation(ident=p[2], attribute_decl_list=p[4])
    else:
        p[0] = maker.make_relation(ident=p[2], attribute_decl_list=[])


def p_directive(p):
    '''directive : INPUT_DECL ident_list
            | OUTPUT_DECL ident_list'''
    p[0] = maker.make_directive(io=p[1], ident_list=p[2])


def p_rule(p):
    '''rule : head IF body DOT'''
    p[0] = maker.make_rule(head=p[1], body=p[3])


def p_fact(p):
    '''fact : atom DOT'''
    p[0] = maker.make_fact(atom=p[1])


# Normally, "atom" and "literal" are used interchangeably
# But, we will use them as follows:
#   "atom" ~~ "positive literal"
#   "literal" ~~ "positive/negative literal"
#   "constraint" ~~ "a special literal of v-o-c form"

def p_head(p):
    '''head : atom'''
    p[0] = p[1]


def p_body(p):
    '''body : conjunction
        | conjunction SEMICOLON conjunction_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def p_conjunction_list(p):
    '''conjunction_list : conjunction
            | conjunction SEMICOLON conjunction_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def p_conjunction(p):
    '''conjunction : item
            | item COMMA item_list'''
    if len(p) == 2:
        p[0] = maker.make_conjunction(items=[p[1]])
    else:
        p[0] = maker.make_conjunction(items=[p[1]] + p[3])


def p_item_list(p):
    '''item_list : item
            | item COMMA item_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def p_item(p):
    '''item : atom
            | negation
            | constraint'''
    p[0] = p[1]


def p_atom(p):
    '''atom : IDENT LPAREN argument_list RPAREN
            | IDENT LPAREN RPAREN'''
    if len(p) == 5:
        p[0] = maker.make_atom(ident=p[1], argument_list=p[3])
    else:
        p[0] = maker.make_atom(ident=p[1], argument_list=[])


def p_negation(p):
    '''negation : NOT atom'''
    p[0] = maker.make_negation(atom=p[2])


def p_constraint(p):
    '''constraint : variable EQ constant
            | variable NE constant
            | variable GT constant
            | variable LT constant
            | variable GE constant
            | variable LE constant'''
    p[0] = maker.make_constraint(variable=p[1], cmp=p[2], constant=p[3])


def p_ident_list(p):
    '''ident_list : IDENT
            | IDENT COMMA ident_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def p_attribute_decl_list(p):
    '''attribute_decl_list : attribute_decl
            | attribute_decl COMMA attribute_decl_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def p_attribute_decl(p):
    '''attribute_decl : IDENT COLON type_name'''
    p[0] = p[3]


def p_type_name(p):
    '''type_name : NUMBER 
            | SYMBOL 
            | IDENT'''
    p[0] = maker.make_type(type_name=p[1])


def p_argument_list(p):
    '''argument_list : argument
            | argument COMMA argument_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def p_argument(p):
    '''argument : variable
            | constant'''
    p[0] = p[1]


def p_variable(p):
    '''variable : IDENT 
            | UNDERSCORE'''
    p[0] = maker.make_variable(variable=p[1])


def p_constant(p):
    '''constant : STRING
            | INTEGER'''
    p[0] = maker.make_constant(constant=p[1])


def p_error(p):
    print("Syntax error in input" + str(p))
    exit()


def parse_program(text):
    lex()
    return yacc.yacc(start='program').parse(text)


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        data = """//comment
        .type abc
            .type xyz <: abc
            .type mnp = symbol
            .decl ans(x: number, y: symbol)
            .input A, B
            .input C

                .output A
                .output A,B,C,D
                //acbdef
            ans(v0, v1, v2, v3) :- input1(v0, v1, v2, v3); inv(v1), v1 >= 1.
            inv(v2) :- correct(v0), !input1(v1, v2, v3, v0), Rule(1).
            ans(v1, v2, v3, v0) :- correct(v0), input1(v1, v2, v3, v0), v0 = "2", v3 = "45".
                    """
    else:
        filename = sys.argv[1]
        try:
            data = open(filename, 'r').read()
        except FileNotFoundError:
            print(f'FileNotFoundError: {filename}')
            exit(-1)

    prog = parse_program(data)
    print('====== ORIGINAL ======')
    print(prog)

    print('\n\n\n')
    print('====== CLEAN ======')

    from synthbx.core.handler import clean_relation_rule
    clean_relation_rule(prog)
    prog.clean_relation('ans')

    t = prog.clone()
    print(t)
