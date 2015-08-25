"""
auteur: Folaefolc
date: 24-08-2015
licence: MIT
version: 0.0.1
"""

import os.path
import sys
import re
import math
import operator as op


start_token = '('
end_token = ')'
comment = "<!"
Symbol = str
List = list
Number = (int, float)
language_name = 'ArkPov'
ext = '.akp'


class Env(dict):
    def __init__(self, parms=(), args=(), outer=None):
        super().__init__(self)
        self.update(zip(parms, args))
        self.outer = outer

    def __getitem__(self, var):
        return dict.__getitem__(self, var) if (var in self) else raise_error('KeyError', '\'' + var + '\' doesn\'t exist')

    def find(self, var):
        if var in self:
            return self
        elif self.outer is not None:
            return self.outer.outer.find(var)
        else:
            raise_error('KeyError', '\'' + var + '\' doesn\'t exist')
            return {var: None}


class Procedure(object):
    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env

    def __call__(self, *args):
        return eval_code(self.body, Env(self.parms, args, self.env))


class Buffer:
    def __init__(self):
        self.buffer = ""

    def add(self, txt, sep="\n"):
        self.buffer += str(txt) + sep

    def __str__(self):
        return self.buffer


buffer = Buffer()


def print_(*args, end='\r\n', file=sys.stdout, sep=' ', flush=False):
    for i in args:
        file.write(str(i) + sep)
        buffer.add(str(i), sep)
    file.write(end)
    if flush:
        file.flush()


def raise_error(err_type, msg):
    print_(err_type, ':', msg)


def return_success(success_type, msg):
    print_(success_type, ':', msg)


def to_py(code):
    work = ""
    for i in code:
        if isinstance(i, list):
            work += "(" + to_py(i) + ")"
        else:
            work += i + " "
    return work


def tokenize(chars):
    work = chars
    #work = re.sub(comment + ".+", '', work)
    work = work.replace(start_token, ' ( ').replace(end_token, ' ) ').split()
    return work


def parse(program):
    return read_from_tokens(tokenize(program))


def read_from_tokens(tokens):
    if len(tokens) == 0:
        return raise_error('SyntaxError', 'Unexpected EOF while reading')
    token = tokens.pop(0)
    if start_token == token:
        ast = []
        while tokens[0] != end_token:
            ast.append(read_from_tokens(tokens))
        tokens.pop(0)  # pop off ')'
        return ast
    elif token == end_token:
        return raise_error('SyntaxError', 'Unexpected ' + end_token)
    elif token == comment:
        pass
    else:
        return atom(token)


def atom(token):
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)


def standard_env():
    global env
    env = Env()
    env.update(vars(math))  # sin, cos, sqrt, pi, ...
    env.update({
        '+': op.add,
        '-': op.sub,
        '*': op.mul,
        '/': op.truediv,
        '>': op.gt,
        '<': op.lt,
        '>=': op.ge,
        '<=': op.le,
        '=': op.eq,
        'abs': abs,
        'append': op.add,
        'begin': lambda *x: x[-1],
        'car': lambda x: x[0],
        'cdr': lambda x: x[1:],
        'cons': lambda x, y: [x] + y,
        'eq?': op.is_,
        'equal?': op.eq,
        'length': len,
        'list': lambda *x: list(x),
        'list?': lambda x: isinstance(x, list),
        'map': map,
        'max': max,
        'min': min,
        'not': op.not_,
        'null': None,
        'null?': lambda x: x == [],
        'number?': lambda x: isinstance(x, Number),
        'procedure?': callable,
        'round': round,
        'symbol?': lambda x: isinstance(x, Symbol),
        'type': lambda x: type(x),
        'include': lambda x: (eval_code(parse(open("Lib/" + x + ext, 'r').read())), return_success("IncludeSuccess", "Successful loading of '" + x + "'"))
            if os.path.exists("Lib/" + x + ext)
                  else ((eval_code(parse(open(x + ext, 'r').read())), return_success("IncludeSuccess", "Successful loading of '" + x + "'"))
                          if os.path.exists(x + ext)
                                  else raise_error("FileNotFoundError", "File '" + x + "' doesn't seem to exist"))
    })
    return env


global_env = standard_env()

help_lst = [
    [("quote", "exp"), "Display exp"],
    [("display",  "var"), "Display the value of var"],
    [("lambda", "(var...)", "body"), "Create a lambda with parameter(s) var... and body as the code"],
    [("if", "test", "conseq", "alt"), "If test is true, it will executed conseq. Else, alt will be executed"],
    [("?", "test"), "If test is true, it will return 1. Else, it will return 0"],
    [("define", "var", "exp"), "Define var and set its value as exp. If var already exists, it will raise an exception"],
    [("pyexc", "prgm"), "Execute prgm as a python code"],
    [("include", "file"), "Include file. If file is not in the standart lib folder, it will search in the current directory for file"],
    [("set!", "var", "exp"), "Set the value of var as exp. If var doesn't exist, it will raise an exception"]
]


def eval_code(x, env=global_env):
    if isinstance(x, Symbol):  # variable reference
        return env.find(x)[x]
    elif not isinstance(x, List):  # constant literal
        return x
    elif x[0] == help_lst[0][0][0]:
        if len(x) >= len(help_lst[0][0]):
            (_, *exp) = x
            return ' '.join(exp)
        else:
            return raise_error("ArgumentError", "'" + x[0] + "' need at least " + str(len(help_lst[0][0]) - 1) + " arguments")
    elif x[0] == help_lst[1][0][0]:
        if len(x) == len(help_lst[1][0]):
            (_, exp) = x
            return env[exp]
        else:
            return raise_error("ArgumentError", "'" + x[0] + "' need exactly " + str(len(help_lst[1][0]) - 1) + " arguments")
    elif x[0] == help_lst[2][0][0]:
        if len(x) == len(help_lst[2][0]):
            (_, parms, body) = x
            return Procedure(parms, body, env)
        else:
            return raise_error("ArgumentError", "'" + x[0] + "' need exactly " + str(len(help_lst[2][0]) - 1) + " arguments")
    elif x[0] == help_lst[3][0][0]:  # (if test conseq alt)
        if len(x) == len(help_lst[3][0]):
            (_, test, conseq, alt) = x
            exp = conseq if eval_code(test, env) else alt
            return eval_code(exp, env)
        else:
            return raise_error("ArgumentError", "'" + x[0] + "' need exactly " + str(len(help_lst[3][0]) - 1) + " arguments")
    elif x[0] == help_lst[4][0][0]:
        if len(x) == len(help_lst[4][0]):
            (_, test) = x
            exp = 1 if eval_code(test, env) else 0
            return exp
        else:
            return raise_error("ArgumentError", "'" + x[0] + "' need exactly " + str(len(help_lst[4][0]) - 1) + " arguments")
    elif x[0] == help_lst[5][0][0]:
        if len(x) == len(help_lst[5][0]):
            (_, var, exp) = x
            if var not in env.keys():
                env[var] = eval_code(exp, env)
            else:
                return raise_error("DefineError", "Can't override existing variable. Use set! instead")
        else:
            return raise_error("ArgumentError", "'" + x[0] + "' need exactly " + str(len(help_lst[5][0]) - 1) + " arguments")
    elif x[0] == help_lst[6][0][0]:
        if len(x) >= len(help_lst[6][0]):
            (_, *exp) = x
            exec(to_py(exp))
        else:
            return raise_error("ArgumentError", "'" + x[0] + "' need at least " + str(len(help_lst[6][0]) - 1) + " arguments")
    elif x[0] == help_lst[7][0][0]:
        if len(x) == len(help_lst[7][0]):
            (_, exp) = x
            env[_](exp)
        else:
            return raise_error("ArgumentError", "'" + x[0] + "' need exactly " + str(len(help_lst[7][0]) - 1) + " arguments")
    elif x[0] == help_lst[8][0][0]:
        if len(x) == len(help_lst[8][0]):
            (_, var, exp) = x
            if var in env.keys():
                env[var] = eval_code(exp, env)
            else:
                return raise_error("SetError", "Can't overwrite a non existing variable. Use define instead")
        else:
            return raise_error("ArgumentError", "'" + x[0] + "' need exactly " + str(len(help_lst[8][0]) - 1) + " arguments")
    elif x[0] == 'help':
        if len(x) == 1:
            for line in help_lst:
                print('(', end='')
                for i in range(len(line[0])):
                    print(line[0][i], end='')
                    if i != len(line[0]) - 1:
                        print('', end=' ')
                    else:
                        print(') : ', end='')
                print(line[1])
        if len(x) == 2:
            (_, exp) = x
            tmp = []
            for line in help_lst:
                if line[0][0] == exp:
                    tmp = line
                    break
            if tmp:
                print('(', end='')
                for i in range(len(tmp[0])):
                    print(tmp[0][i], end='')
                    if i != len(tmp[0]) - 1:
                        print('', end=' ')
                    else:
                        print(') : ', end='')
                print(tmp[1])
            else:
                return raise_error("DocumentationError", "Couldn't find documentation for '" + exp + "'")
    else:  # (proc arg ...)
        proc = eval_code(x[0], env)
        args = [eval_code(arg, env) for arg in x[1:]]
        return proc(*args)


def loop():
    std_prompt = language_name + ' > '
    not_eof_prompt = language_name + ' \' '

    prompt = std_prompt
    code = ""

    while True:
        code = input(prompt) if prompt != not_eof_prompt else code + " " + input(prompt)

        if code[-1] != end_token:
            prompt = not_eof_prompt

            if code in env.keys():
                prompt = std_prompt

        if prompt == std_prompt or code[-1] == end_token:
            prompt = std_prompt

            parsed = parse(code)
            val = eval_code(parsed)

            if val is not None:
                print_(schemestr(val))


def schemestr(exp):
    if isinstance(exp, list):
        return '(' + ' '.join(map(schemestr, exp)) + ')'
    else:
        return str(exp)


if __name__ == '__main__':
    arguments = []
    try:
        arguments = sys.argv[1:]
        script = arguments[0]
        with open(script, 'r') as code_:
            print(eval_code(parse(code_.read())))
            return_success('ReadingSuccess', "File '" + script + "' successfully loaded and read")
    except IndexError:
        pass

    loop()