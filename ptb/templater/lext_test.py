from ptb.templater import lex

word_templater_parser = lex.TemplaterParser()
while True:
    try:
        s = input('calc > ')
    except EOFError:
        break
    if not s:
        continue
    b = word_templater_parser.parse(s)
    print(b)