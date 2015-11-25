import constants


def tokenize(code: str):
    return code.replace(L_TOKEN, " " + L_TOKEN + " ").replace(R_TOKEN, " " + R_TOKEN + " ").split()


def parser(tokens):
    if not len(tokens):
        print(ERROR + "Unexpected EOF while parsing")
        return R_TOKEN
    
    token = tokens.pop(0)
    if token == L_TOKEN:
        ast = []
        while tokens[0] != R_TOKEN:
            ast.append(parser(tokens))
        tokens.pop(0)
        return ast
    elif token == R_TOKEN:
        print(ERROR + "Unexpected " + R_TOKEN + " while parsing")
        return ""
    else:
        return atom(token)


def atom(code: str):
    try:
        return float(code)
    except ValueError:
        try:
            return int(code)
        except ValueError:
            return code