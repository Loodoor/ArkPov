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
        return dict.__getitem__(self, var) if (var in self) else raise_error('KeyError', var + ' doesn\'t exist')

    def find(self, var):
        if var in self:
            return self
        elif self.outer is not None:
            return self.outer.outer.find(var)
        else:
            raise_error('KeyError', var + ' doesn\'t exist')
            return {var: None}


class Procedure(object):
    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env

    def __call__(self, *args):
        return eval_code(self.body, Env(self.parms, args, self.env))


def raise_error(err_type, msg):
    print(err_type, ':', msg)


def return_success(success_type, msg):
    print(success_type, ':', msg)


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
        return raise_error('SyntaxError', 'Unexpected )')
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


def eval_code(x, env=global_env):
    if isinstance(x, Symbol):  # variable reference
        return env.find(x)[x]
    elif not isinstance(x, List):  # constant literal
        return x
    elif x[0] == 'quote':  # (quote exp)
        (_, *exp) = x
        return ' '.join(exp)
    elif x[0] == 'display':  # (displar exp)
        (_, exp) = x
        return env[exp]
    elif x[0] == 'lambda':  # (lambda (var...) body)
        (_, parms, body) = x
        return Procedure(parms, body, env)
    elif x[0] == 'if':  # (if test conseq alt)
        (_, test, conseq, alt) = x
        exp = conseq if eval_code(test, env) else alt
        return eval_code(exp, env)
    elif x[0] == '?':  # (? test) -> 1 | 0
        (_, test) = x
        exp = 1 if eval_code(test, env) else 0
        return exp
    elif x[0] == 'define':  # (define var exp)
        (_, var, exp) = x
        env[var] = eval_code(exp, env)
    elif x[0] == 'pyexc':  # (pyexc exp)
        (_, *exp) = x
        exec(to_py(exp))
    elif x[0] == 'include':  # (include file)
        (_, exp) = x
        env[_](exp)
    else:  # (proc arg ...)
        proc = eval_code(x[0], env)
        args = [eval_code(arg, env) for arg in x[1:]]
        return proc(*args)


def rep(prompt):
    val = eval_code(parse(input(prompt)))
    if val is not None:
        print(schemestr(val))
    return val


def repl():
    std_prompt = language_name + ' > '
    not_eof_prompt = language_name + ' \' '

    while True:
        if True:
            rep(std_prompt)
        else:
            rep(not_eof_prompt)


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
        with open(script, 'r') as code:
            print(eval_code(parse(code.read())))
            return_success('ReadingSuccess', "File '" + script + "' successfully loaded and read")
    except IndexError:
        pass

    repl()