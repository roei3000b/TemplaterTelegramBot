import os
import ply.lex as lex
import ply.yacc as yacc
from ptb.templater import utils

class Parser:
    tokens = ()
    precedence = ()

    def __init__(self, names=None, **kw):
        self.debug = kw.get('debug', 0)
        self.names = names or {}
        try:
            modname = os.path.split(os.path.splitext(__file__)[0])[
                          1] + "_" + self.__class__.__name__
        except:
            modname = "parser" + "_" + self.__class__.__name__
        # self.debugfile = modname + ".dbg"
        # print self.debugfile

        # Build the lexer and parser
        lex.lex(module=self, debug=self.debug)
        yacc.yacc(module=self,
                  debug=self.debug,
                  )

    def parse(self, s, **kwargs):
        b = yacc.parse(s, **kwargs)
        return b

    def set_names(self, names):
        self.names = names


class WordTemplaterParser(Parser):

    tokens = (
        'NAME', 'TIME', 'NUMBER', 'UP', 'DOWN',
    )

    literals = ['=', '+', '-', '*', '/', '(', ')']

    # Tokens
    def t_UP(self, t):
        r'UP'
        return t

    def t_DOWN(self, t):
        r'DOWN'
        return t

    def t_NAME(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        return t

    def t_TIME(self, t):
        r'([0-1][0-9]|2[0-3]):[0-5][0-9]'
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    t_ignore = " \t"


    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")


    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)


    precedence = (
        ('left', '+', '-'),
        ('left', '*', '/'),
        ('right', 'UMINUS'),
    )

    def p_statement_assign(self, p):
        '''statement : NAME "=" expression
                       | NAME "=" TIME'''
        self.names[p[1]] = p[3]
        p[0] = p[3]


    def p_statement_expr(self, p):
        'statement : expression'
        p[0] = p[1]

    def p_expression_binop(self, p):
        '''expression : expression '+' expression
                      | expression '-' expression
                      | expression '*' expression
                      | expression '/' expression'''
        if p[2] == '+':
            if utils.is_number(p[1]) and utils.is_number(p[3]):
                p[0] = p[1] + p[3]
            else:
                p[0] = utils.add_minutes_to_time(p[1], p[3])
        elif p[2] == '-':
            if utils.is_number(p[1]) and utils.is_number(p[3]):
                p[0] = p[1] - p[3]
            else:
                p[0] = utils.add_minutes_to_time(p[1], -p[3])
        elif p[2] == '*':
            p[0] = p[1] * p[3]
        elif p[2] == '/':
            p[0] = p[1] / p[3]



    def p_expression_uminus(self, p):
        "expression : '-' expression %prec UMINUS"
        p[0] = -p[2]

    def p_expression_down(self, p):
        "expression : DOWN '(' expression ')'"
        p[0] = utils.round_down_to_nearest_5_minutes(p[3])


    def p_expression_up(self, p):
        "expression : UP '(' expression ')'"
        p[0] = utils.round_up_to_nearest_5_minutes(p[3])

    def p_expression_group(self, p):
        "expression : '(' expression ')'"
        p[0] = p[2]


    def p_expression_number(self, p):
        "expression : NUMBER"
        p[0] = p[1]

    def p_expression_time(self, p):
        "expression : TIME"
        p[0] = p[1]


    def p_expression_name(self, p):
        "expression : NAME"
        try:
            p[0] = self.names[p[1]]
        except LookupError:
            print("Undefined name '%s'" % p[1])
            p[0] = 0


    def p_error(self, p):
        if p:
            print("Syntax error at '%s'" % p.value)
        else:
            print("Syntax error at EOF")
