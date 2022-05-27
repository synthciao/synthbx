import ply.yacc as yacc
import re
from synthbx.parser.schema.lexer import tokens, lex, t_INVENT
import synthbx.parser.maker as maker
from synthbx.ast.relation import DirectiveType


def p_schema(p):
    '''schema : relation_list'''
    p[0] = maker.make_schema(relation_list=p[1])


def p_relation_list(p):
    '''relation_list : directive_relation
            | relation_list directive_relation'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_directive_relation(p):
    '''directive_relation : INPUT relation
            | INVENT relation
            | relation'''
    if len(p) == 3:
        p[0] = p[2]
        if not re.match(t_INVENT, p[1]):
            p[0].directives = [DirectiveType.INPUT]
            p[0].invent = False
    else:
        p[0] = p[1]
        p[0].invent = False


def p_relation(p):
    '''relation : IDENT LPAREN type_list RPAREN'''
    p[0] = maker.make_relation(ident=p[1], attribute_decl_list=p[3])


def p_type_list(p):
    '''type_list : type
            | type COMMA type_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def p_type(p):
    '''type : IDENT'''
    p[0] = maker.make_type(type_name=p[1].lower())


def p_error(p):
    print("Syntax error in input" + str(p))
    exit()


def parse_schema(text):
    lex()
    return yacc.yacc(start='schema').parse(text)


if __name__ == '__main__':

    text = """*LE20130201(date)
        *GE20130215(date)
        *input1(yrq,date,date)
        # hello
        //world
        /*this is a schema*/
        +inv(date)
        +abc(yrq)
        /*are you
        ok?*/
        ans(yrq)
        """

    schema = parse_schema(text)
    source, view, invent = schema.partition()
    [print('SOURCE: ' + r.str_of_schema()) for r in source]
    [print('INVENT: ' + r.str_of_schema()) for r in invent]
    [print('VIEW: ' + r.str_of_schema()) for r in view]

    for r in source:
        print(r)
        for t in r.schema:
            print(f'{t} : {type(t)}')
