import ply.lex

tokens = [
    'IDENT',
    'INPUT',
    'INVENT',
    'COMMA',
    'LPAREN', 'RPAREN'
]

t_IDENT = r'[A-Za-z][A-Za-z0-9_]*'
t_INPUT = r'\*'
t_INVENT = r'\+'
t_COMMA = r','
t_LPAREN = r'\('
t_RPAREN = r'\)'

t_ignore = ' \t'


def t_newline(t):
    r'\n'
    t.lexer.lineno += 1


def t_comment(t):
    r'(--|\#|//).*\n'
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

    tokens = []
    while True:
        t = lexer.token()
        if not t:
            break
        tokens.append(t)
    return tokens


if __name__ == '__main__':
    data = """*LE20130201(date)
        *GE20130215(date)
        *input1(yrq,date,date)
        #hello
        //world
        /*this is a schema*/
        +inv(date)
        +abc(yrq)
        /*are you
        ok?*/
        ans(yrq)
        """
    tokens = tokenize(data)
    [print(t) for t in tokens]
