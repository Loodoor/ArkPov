import os
import sys
import math
import operator as op
from my_parser import *
from classes import *


class Procedure(object):
    "A user-defined Scheme procedure."
    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env
    
    def __call__(self, *args): 
        return evaluate(self.body, Env(self.parms, args, self.env))


def evaluate(code: list, env: Env):
    if isinstance(code, str):
        return env.find(code)[code]
    elif not isinstance(code, list):
        return code
    # gestion des mots clés
    elif code[0] == 'quote':
        _, *exp = code
        return ' '.join(exp)
    elif code[0] == 'if':
        if len(code) == 4:
            _, test, conseq, alt = code
            exp = conseq if evaluate(test, env) else alt
            return eval(exp, env)
        elif len(code) == 3:
            _, test, conseq = code
            exp = conseq if evaluate(test, env) else not conseq
            print(WARNING + "the alternative was missing, so Ark's parser decide to return not conseq if the test would fail")
            return eval(exp, env)
    elif code[0] == 'let':
        _, var, exp = code
        if var not in env.keys():
            env[var] = evaluate(exp, env)
        else:
            print(ERROR + var + " already exist. Impossible to overwrite it. Use set instead")
    elif code[0] == 'set':
        _, var, exp = code
        if var in env.keys():
            env[var] = evaluate(exp, env)
        else:
            print(ERROR + var + " doesn't exist. Use let to create it")
    elif code[0] == 'lambda':
        _, parms, body = code
        return Procedure(parms, body, env)
    # gestion des procédures et callable
    else:
        proc = evaluate(code[0], env)
        args = [evaluate(arg, env) for arg in code[1:]]
        return proc(*args)


def main(env: dict):
    while True:
        line = input("Ark:: ")
        ret = evaluate(parser(tokenize(line)), env=env)
        
        if ret:
            if isinstance(ret, list):
                print(''.join(ret))
            else:
                print(ret)


if __name__ == '__main__':
    env = Env()
    env.update(vars(math)) # sin, cos, sqrt, pi, ...
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
        'null?': lambda x: x == [],
        'number?': lambda x: isinstance(x, (int, float)),
        'procedure?': callable,
        'round': round,
        'symbol?': lambda x: isinstance(x, str)
    })
    
    args = sys.argv
    if len(args) > 1:
        args = args[1:]
        filename = args[0]
        if len(args) > 1:
            do_not_close = args[0]
        if os.path.exists(filename):
            with open(filename) as file:
                pass
        if do_not_close:
            main(env)
    else:
        main(env)