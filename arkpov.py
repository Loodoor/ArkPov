"""
auteur: Folaefolc
date: 24-08-2015
licence: MIT
version: 0.0.1
"""

import os.path
import sys
import math
import operator as op
import re
import time


start_token = '(', '['
end_token = ')', ']'
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
        return dict.__getitem__(self, var) if (var in self) \
            else raise_error('KeyError', '\'' + str(var) + '\' doesn\'t exist')

    def find(self, var):
        if var in self:
            return self
        elif self.outer is not None:
            return self.outer.find(var)
        else:
            raise_error('KeyError', '\'' + str(var) + '\' doesn\'t exist')
            return {var: None}


class Procedure(object):
    def __init__(self, parms, body, envi, desc=""):
        self.parms, self.body, self.env, self.desc = parms, body, envi, desc

    def __call__(self, *args):
        return eval_code(self.body, Env(self.parms, args, self.env))

    def doc(self):
        return self.desc


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


def proc_to_py(code):
    l = ""
    for i in code:
        if not isinstance(i, list):
            l += i
        else:
            l += "(" + proc_to_py(i) + ")"
    return l


def tokenize(chars):
    work = chars
    for i in range(2):
        work = work.replace(start_token[i], ' ( ').replace(end_token[i], ' ) ')
    work = work.split()
    return work


def parse(program):
    return read_from_tokens(tokenize(program))


def read_from_tokens(tokens):
    if len(tokens) == 0:
        return raise_error('SyntaxError', 'Unexpected EOF while reading')
    token = tokens.pop(0)
    if token in start_token:
        ast = []
        while tokens[0] not in end_token:
            ast.append(read_from_tokens(tokens))
        tokens.pop(0)  # pop off ')'
        return ast
    elif token in end_token:
        return raise_error('SyntaxError', 'Unexpected ' + token)
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


def join(lst, sep=''):
    work = ""
    if type(lst) == tuple:
        for i in lst[0]:
            work += Symbol(i) + sep
    else:
        for i in lst:
            work += Symbol(i) + sep
    if sep != '':
        work = work[:-1]
    return work


def standard_env():
    global env
    env = Env()
    env.update(vars(math))  # sin, cos, sqrt, pi, ...
    env.update({
        '+': op.add,
        '-': op.sub,
        '*': op.mul,
        '/': op.truediv,
        '//': op.floordiv,
        '%': op.mod,
        '>': op.gt,
        '<': op.lt,
        '>=': op.ge,
        '<=': op.le,
        '=': op.eq,
        '!=': op.ne,
        'not': op.not_,
        'append': op.add,
        'begin': lambda *x: x[-1],
        'car': lambda x: x[0],
        'cdr': lambda x: x[1:],
        'cons': lambda x, y: [x] + y,
        'eq?': op.is_,
        'equal?': op.eq,
        'length': len,
        'list': lambda *x: list(x),
        'list?': lambda x: isinstance(x, List),
        'map': map,
        'max': max,
        'min': min,
        'time': time.time,
        'null': None,
        'read': lambda x: open(join(x), "r").read(),
        'write': lambda x: open(join(x[0]), "w").write(eval_code(x[1])),
        'splittext': lambda x: eval_code(x[0], env).split(join(x[1:])),
        'null?': lambda x: x == [],
        'number?': lambda x: isinstance(x, Number),
        'procedure?': callable,
        'round': round,
        'symbol': lambda *x: join(x, ' '),
        'symbol?': lambda x: isinstance(x, Symbol),
        'type': lambda x: type(x),
        'include': lambda x: (eval_code(parse(open("Lib/" + x + ext, 'r').read())),
                              return_success("IncludeSuccess", "Successful loading of '" + x + "'"))
        if os.path.exists("Lib/" + x + ext)
        else ((eval_code(parse(open(x + ext, 'r').read())),
               return_success("IncludeSuccess", "Successful loading of '" + x + "'"))
              if os.path.exists(x + ext)
              else ((env.update({re.match(r'def (?P<name>.+)\(.+\):',
                                          open("Lib/" + x + ".py", "r").read())
                                .groupdict()['name']: open("Lib/" + x + ".py", "r").read()}),
                     return_success("IncludeSuccess", "Successful loading of '" + x + "'"))
                    if os.path.exists("Lib/" + x + ".py")
                    else raise_error("FileNotFoundError", "File '" + x + "' doesn't seem to exist")))
    })
    return env


global_env = standard_env()

help_lst = [
    [("say", "exp"), "Display exp"],
    [("show", "var"), "Display the value of var"],
    [("lambda", "(var...)", "body"), "Create a lambda with parameter(s) var... and body as the code"],
    [("if", "test", "conseq", "alt"), "If test is true, it will executed conseq. Else, alt will be executed"],
    [("?", "test"), "If test is true, it will return 1. Else, it will return 0"],
    [("new", "var", "exp"),
     "Define var and set its value as exp. If var already exists, it will raise an exception"],
    [("pyexc", "prgm"), "Execute prgm as a python code"],
    [("include", "file"),
     "Include file. If file is not in the standart lib folder, it will search in the current directory for file"],
    [("set!", "var", "exp"), "Set the value of var as exp. If var doesn't exist, it will raise an exception"],
    [("defun", "name", "(var...)", "desc", "exp"),
     "Create a function called name, with parameter(s) var..., "
     "desc as the description of the function (optional), and exp as the code to run"],
    [("until", "test", "exp", "end"),
     "While the test is false, exp continue to run. end is executed when the test is true. "
     "Prefer boolean test who is shorter"]
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
            return raise_error("ArgumentError",
                               "'" + x[0] + "' need at least " + str(len(help_lst[0][0]) - 1) + " arguments")
    elif x[0] == help_lst[1][0][0]:
        if len(x) == len(help_lst[1][0]):
            (_, exp) = x
            return env.find(exp)[exp]
        else:
            return raise_error("ArgumentError",
                               "'" + x[0] + "' need exactly " + str(len(help_lst[1][0]) - 1) + " arguments")
    elif x[0] == help_lst[2][0][0]:
        if len(x) == len(help_lst[2][0]):
            (_, parms, body) = x
            return Procedure(parms, body, env)
        else:
            return raise_error("ArgumentError",
                               "'" + x[0] + "' need exactly " + str(len(help_lst[2][0]) - 1) + " arguments")
    elif x[0] == help_lst[3][0][0]:
        if len(x) == len(help_lst[3][0]):
            (_, test, conseq, alt) = x
            exp = conseq if eval_code(test, env) else alt
            return eval_code(exp, env)
        else:
            return raise_error("ArgumentError",
                               "'" + x[0] + "' need exactly " + str(len(help_lst[3][0]) - 1) + " arguments")
    elif x[0] == help_lst[4][0][0]:
        if len(x) == len(help_lst[4][0]):
            (_, test) = x
            exp = 1 if eval_code(test, env) else 0
            return exp
        else:
            return raise_error("ArgumentError",
                               "'" + x[0] + "' need exactly " + str(len(help_lst[4][0]) - 1) + " arguments")
    elif x[0] == help_lst[5][0][0]:
        if len(x) == len(help_lst[5][0]):
            (_, var, exp) = x
            if var not in env.keys():
                env[var] = eval_code(exp, env)
            else:
                return raise_error("DefineError",
                                   "Can't override existing variable. Use " + str(help_lst[8][0][0]) + " instead")
    elif x[0] == help_lst[6][0][0]:
        if len(x) >= len(help_lst[6][0]):
            (_, *exp) = x
            return exec(to_py(exp))
        else:
            return raise_error("ArgumentError",
                               "'" + x[0] + "' need at least " + str(len(help_lst[6][0]) - 1) + " arguments")
    elif x[0] == help_lst[7][0][0]:
        if len(x) == len(help_lst[7][0]):
            (_, exp) = x
            env[_](exp)
        else:
            return raise_error("ArgumentError",
                               "'" + x[0] + "' need exactly " + str(len(help_lst[7][0]) - 1) + " arguments")
    elif x[0] == help_lst[8][0][0]:
        if len(x) == len(help_lst[8][0]):
            (_, var, exp) = x
            if var in env.keys():
                env[var] = eval_code(exp, env)
            else:
                return raise_error("SetError", "Can't overwrite a non existing variable. Use define instead")
        else:
            return raise_error("ArgumentError",
                               "'" + x[0] + "' need exactly " + str(len(help_lst[8][0]) - 1) + " arguments")
    elif x[0] == help_lst[9][0][0]:
        if len(x) == len(help_lst[9][0]):
            (_, var, params, desc, exp) = x
            env[var] = Procedure(params, exp, env, desc=desc)
        elif len(x) == len(help_lst[9][0]) - 1:
            (_, var, params, exp) = x
            env[var] = Procedure(params, exp, env)
        else:
            return raise_error("ArgumentError",
                               "'" + x[0] + "' need exactly " + str(len(help_lst[9][0]) - 1) + " arguments")
    elif x[0] == help_lst[10][0][0]:
        if len(x) == len(help_lst[10][0]):
            (_, test, body, end) = x
            while True:
                if eval_code(test, env):
                    val = eval_code(body, env)
                    if val is not None:
                        print_(schemestr(val))
                else:
                    val = eval_code(end, env)
                    if val is not None:
                        print_(schemestr(val))
                    break
        elif len(x) == len(help_lst[10][0]) - 1:
            (_, test, body) = x
            while eval_code(test, env):
                val = eval_code(body, env)
                if val is not None:
                    print_(schemestr(val))
        else:
            return raise_error("ArgumentError",
                               "'" + x[0] + "' need at least " + str(len(help_lst[10][0]) - 2) + " arguments")
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
            tmp = [0, 0, 0]
            for line in help_lst:
                if line[0][0] == exp:
                    tmp = line
                    break
            if tmp != [0, 0, 0]:
                print('(', end='')
                for i in range(len(tmp[0])):
                    print(tmp[0][i], end='')
                    if i != len(tmp[0]) - 1:
                        print('', end=' ')
                    else:
                        print(') : ', end='')
                print(tmp[1])
            if tmp == [0, 0, 0]:
                for k, v in env.items():
                    if isinstance(v, Procedure) and k == exp:
                        desc = v.doc()
                        if desc:
                            print_(desc)
                            break
                        else:
                            return raise_error("DocumentationError", "Documentation missing in '" + k + "'")
            else:
                return raise_error("DocumentationError", "Couldn't find documentation for '" + exp + "'")
    else:  # (proc arg ...)
        if not isinstance(env.find(x[0])[x[0]], str):
            proc = eval_code(x[0], env)
            if x[0] != "symbol" and x[0] != "read" and x[0] != "write" and x[0] != "splittext":
                args = [eval_code(arg, env) for arg in x[1:]]
                try:
                    return proc(*args)
                except TypeError:
                    args.append(1)
                    return proc(*args)
            else:
                return proc(x[1:])
        else:
            (_, *var) = x
            args = re.match(r"def (?P<name>.+)\((?P<args>.+)\):", env[_]).groupdict()['args']\
                .replace(',', '-').strip().split('-')
            if len(args) <= len(var):
                dctargs = {k: 0 for k in args}
                i = 0
                for k, v in dctargs.items():
                    dctargs[k] = var[i]
                    i += 1
                tmp = env[_] + "\nprint(" + str(_) + "("
                for k, v in dctargs.items():
                    tmp += str(v) + ", "
                tmp = tmp[:-2:] + "))"

                exec(tmp)
            else:
                return raise_error("ArgumentError", "'" + str(_) + "' need at least " + str(len(args)) + " arguments")


def loop():
    std_prompt = language_name + ' > '
    not_eof_prompt = language_name + ' \' '

    prompt = std_prompt
    code = ""

    while True:
        code = input(prompt) if prompt != not_eof_prompt else code + " " + input(prompt)

        if code.count(start_token[0]) + code.count(start_token[1]) != code.count(end_token[0]) + code.count(end_token[1]):
            prompt = not_eof_prompt

            if code in env.keys():
                prompt = std_prompt

        if code.count(start_token[0]) + code.count(start_token[1]) == code.count(end_token[0]) + code.count(end_token[1])\
                and code.strip()[:2] != comment:
            prompt = std_prompt

            parsed = parse(code)
            val = eval_code(parsed)

            if val is not None:
                print_(schemestr(val))


def schemestr(exp):
    if isinstance(exp, list):
        return Symbol(exp)[1:-1]  # '(' + ' '.join(map(schemestr, exp)) + ')'
    else:
        return str(exp)


if __name__ == '__main__':
    arguments = []
    cont = False
    try:
        arguments = sys.argv[1:]
        script = arguments[0]
        with open(script, 'r') as code_:
            print(eval_code(parse(code_.read())))
            return_success('ReadingSuccess', "File '" + script + "' successfully loaded and read")
        try:
            cont = arguments[1]
            if int(cont):
                loop()
            else:
                pass
        except IndexError:
            pass

    except IndexError:
        pass

    if not arguments:
        loop()