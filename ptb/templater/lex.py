from datetime import datetime, timedelta

tokens = (
    'NAME', 'TIME', 'NUMBER',
)

literals = ['=', '+', '-', '*', '/', '(', ')']

# Tokens

t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'

def t_TIME(t):
    r'([0-1][0-9]|2[0-3]):[0-5][0-9]'
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

t_ignore = " \t"


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
import ply.lex as lex
lex.lex()

# Parsing rules

precedence = (
    ('left', '+', '-'),
    ('left', '*', '/'),
    ('right', 'UMINUS'),
)

# dictionary of names
names = {}

def add_minutes_to_time(time_str, minutes):
    datetime_obj = datetime.strptime(time_str, '%H:%M')
    new_datetime_obj = datetime_obj + timedelta(minutes=minutes)
    return new_datetime_obj.time().strftime('%H:%M')

def p_statement_assign(p):
    '''statement : NAME "=" expression
                   | NAME "=" TIME'''
    names[p[1]] = p[3]


def p_statement_expr(p):
    'statement : expression'
    print(p[1])

def get_args_order(x, y):
    if is_number(x):
        return y,x
    return x,y

def is_number(x):
    return type(x) is int


def p_expression_binop(p):
    '''expression : expression '+' expression
                  | expression '-' expression
                  | expression '*' expression
                  | expression '/' expression'''
    if p[2] == '+':
        if is_number(p[1]) and is_number(p[3]):
            p[0] = p[1] + p[3]
        else:
            time_str, minutes = get_args_order(p[1], p[3])
            p[0] = add_minutes_to_time(time_str, minutes)
    elif p[2] == '-':
        if is_number(p[1]) and is_number(p[3]):
            p[0] = p[1] - p[3]
        else:
            time_str, minutes = get_args_order(p[1], p[3])
            p[0] = add_minutes_to_time(time_str, -minutes)
    elif p[2] == '*':
        p[0] = p[1] * p[3]
    elif p[2] == '/':
        p[0] = p[1] / p[3]



def p_expression_uminus(p):
    "expression : '-' expression %prec UMINUS"
    p[0] = -p[2]


def p_expression_group(p):
    "expression : '(' expression ')'"
    p[0] = p[2]


def p_expression_number(p):
    "expression : NUMBER"
    p[0] = p[1]


def p_expression_name(p):
    "expression : NAME"
    try:
        p[0] = names[p[1]]
    except LookupError:
        print("Undefined name '%s'" % p[1])
        p[0] = 0


def p_error(p):
    if p:
        print("Syntax error at '%s'" % p.value)
    else:
        print("Syntax error at EOF")

import ply.yacc as yacc

yacc.yacc()
yacc.parse("enter_time=21:00", debug=True)
yacc.parse("y=10+x+60*(3+5)", debug=True)
yacc.parse("y", debug=True)