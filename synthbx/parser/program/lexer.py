import ply.lex

reserved = {
    'number': 'NUMBER',
    'symbol': 'SYMBOL'
}

tokens = [
    'IDENT',
    'STRING',
    'INTEGER',
    'IF',
    'COMMA',
    'UNDERSCORE',
    'LPAREN',
    'RPAREN',
    'DOT',
    'NOT',
    'EQ',
    'NE',
    'GT',
    'LT',
    'GE',
    'LE',
    'DECL',
    'INPUT_DECL',
    'OUTPUT_DECL',
    'TYPE',
    'SUBTYPE',
    'COLON',
    'SEMICOLON'
] + list(reserved.values())


def t_IDENT(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    t.type = reserved.get(t.value, 'IDENT')
    return t


t_STRING = r'"[^\"]*"'


def t_INTEGER(t):
    r'-?\d+'
    t.value = int(t.value)
    return t


t_IF = r':-'
t_COMMA = r','
t_UNDERSCORE = r'_'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_DOT = r'\.'
t_NOT = r'!'
t_EQ = r'='
t_NE = r'!='
t_GT = r'>'
t_LT = r'<'
t_GE = r'>='
t_LE = r'<='
t_DECL = r'\.decl'
t_INPUT_DECL = r'\.input'
t_OUTPUT_DECL = r'\.output'
t_TYPE = r'\.type'
t_SUBTYPE = r'<:'
t_COLON = r':'
t_SEMICOLON = r';'

t_ignore = ' \t'


def t_newline(t):
    r'\n'
    t.lexer.lineno += 1


def t_comment(t):
    r'//.*\n'
    t.lexer.lineno += 1


def t_c_comment(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')


def t_error(t):
    print(
        f'Lexing error: Illegal character {t.value[0]} found at lineno {t.lexer.lineno} and lexpos {t.lexpos}')
    t.lexer.skip(1)


def lex():
    return ply.lex.lex()


def tokenize(text):
    lexer = lex()
    lexer.input(text)

    toks = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        toks.append(tok)
    return toks


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        data = """.decl A(x: number, y: symbol)
			.input A

			.output A
			//acbdef
			out(v0, v1) :- In1(v1), !in2(v1,v0); x = y, t < z, v0 = 100.
				out(v0, v1) :- in3(v2), out(v3, v4), v4 != "2", v1 > -10.
				"""
    else:
        filename = sys.argv[1]
        try:
            data = open(filename, 'r').read()
        except FileNotFoundError:
            print(f'FileNotFoundError: {filename}')
            exit(-1)

    toks = tokenize(data)
    [print(t) for t in toks]
