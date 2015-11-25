import os
import sys
import math
import operator as op
from constants import *
from parser import *


def evaluate(code: list, env: dict, vars: dict):
    if isinstance(code, str):
        if code in env.keys():
            return env[code]
         elif code in vars.keys():
            return vars[code]
         print(ERROR + code + " not found. Probably this variable doesn't exist.")
         return ""
    elif not isinstance(code, list):
        return code
    # gestion des mots clés
    elif code[0] == 'quote':
        _, *exp = code
        return exp
    elif code[0] == 'if':
        if len(code) == 4:
            _, test, conseq, alt = code
            exp = conseq if evaluate(test, env, vars) else alt
            return eval(exp, env, vars)
        elif len(code) == 3:
            _, test, conseq = code
            exp = conseq if evaluate(test, env, vars) else not conseq
            print(WARNING + "the alternative was missing, so Ark's parser decide to return not conseq if the test would fail")
            return eval(exp, env, vars)
    elif code[0] == 'let':
        _, var, exp = code
        if var not in vars.keys():
            vars[var] = evaluate(exp, env, vars)
        else:
            print(ERROR + var + " already exist. Impossible de overwrite it. Use set instead")
    elif code[0] == 'set':
        _, var, exp = code
        if var in vars.keys():
            vars[var] = evaluate(exp, env, vars)
        else:
            print(ERROR + var + " doesn't exist. Use let to create it")
    # gestion des procédures et callable
    else:
        proc = evaluate(code[0], env, vars)
        args = [evaluate(arg, env, vars) for arg in code[1:]]
        return proc(*args)


def main(env: dict):
    var_env = VarsEnv()
    
    while True:
        line = input("Ark:: ")
        ret = evaluate(parser(tokenize(line)), env=env, vars=var_env)
        
        if ret:
            if isinstance(ret, list):
                print(''.join(ret))
            else:
                print(ret)


if __name__ == '__main__':
    env = dict()
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
        if os.path.exists(filename):
            with open(filename) as file:
                pass
    else:
        main(env)