class Env(dict):
    "An environment: a dict of {'var':val} pairs, with an outer Env."
    def __init__(self, parms, args, *outers):
        self.update(zip(parms, args))
        self.outers = outers
    
    def find(self, var):
        "Find the innermost Env where var appears."
        return self if var in self else (outer.find(var) for outer in self.outer if outer.find(var))


class Procedure(object):
    "A user-defined Scheme procedure."
    def __init__(self, parms, body, *env):
        self.parms, self.body, self.envs = parms, body, env
    
    def __call__(self, *args):
        return evaluate(self.body, Env(self.parms, args, *self.envs))