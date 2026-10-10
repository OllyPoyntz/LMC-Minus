'''Handling for expressions.'''
from collections import defaultdict
from .lexer import Token, TokenList, tokenise
from .lowlink import inline_functions
from .data import data_sect
#High-level functions written in Little Man C-:
high_functions = {}
small = lambda : -999
prio = defaultdict(small, {
    '+':1,
    '-':1,
    '*':2,
    '/':2,
    '%':2,
    '||':3,
    '&&':3,
    '+=':0,
    '-=':0,
    '*=':0,
    #Comparison operators:
    '==':-1,
    '!=':-1,
    '>':-1,
    '<':-1,
    '<=':-1,
    '>=':-1,
    #Operator with negative infinite priority.
    #Ensures that the method used to evaluate expressions terminates.
    '@':float('-inf')
})

operator_functions = {
    '+':'_addnum',
    '-':'_subnum',
    '*':'_mulnum',
    '/':'_divnum',
    '%':'_modnum',
    '+=':'_addnuminplace',
    '-=':'_subnuminplace',
    '*=':'_mulnuminplace',
    '/=':'_divnuminplace',
    '%=':'_modnuminplace',
    '==':'_check_eq',
    '!=':'_check_neq',
    '>':'_check_gt',
    '<':'_check_lt',
    '<=':'_check_lteq',
    '>=':'_check_gteq',
    '||':'_logic_OR',
    '&&':'_logic_AND',
    }
def convert_string_literals(tokens, asm, registers):
    for x in range(len(tokens)):
        if tokens[x].ttype == 'str':
            #Handle string literals:
            strname = data_sect.add_string_literal(tokens[x].data)
            asm += f'LDA load_{strname}\n'
            asm += 'SUB __base_load\n'
            asm += f'STA __reg.{registers}\n'
            tokens[x] = Token(f'__reg.{registers}')
            registers += 1
        elif isinstance(tokens[x], TokenList):
            tokens[x], asm, registers = convert_string_literals(tokens[x], asm, registers)
    return (tokens, asm, registers)
#Returns (assembly, register to find result):
def evaluate_expr(expression, registers = 0) -> tuple:
    '''Recursively generates assembly code to evaluate a function.'''
    asm = ''
    if isinstance(expression, str):
        tokens = tokenise(expression)
    else:
        tokens = expression
    for x in range(len(tokens)):
        t = tokens[x]
        if t.ttype == 'int':
            t.data = '__int.' + str(t.data)
            t.ttype = 'sym'
        elif t.ttype == 'chr':
            t.data = '__int.' + str(ord(t.data))
            t.ttype = 'sym'
    #Convert string literals:
    tokens, newasm, registers = convert_string_literals(tokens, asm, registers)
    asm += newasm
    tokens.append(Token('@'))
    #print(tokens)
    if len(tokens) == 2:
        if (isinstance(tokens[0], TokenList)):
            return evaluate_expr(tokens[0])
        return ('', tokens[0].data)
    #Position in the list of tokens:
    position = 0
    #Priority of the current item:
    cprio = -9999
    #Current operator:
    copr = None
    #Current item:
    citem = None
    #Handle function calls:
    if tokens[0].ttype == 'sym' and isinstance(tokens[1], TokenList):
        #Function call:
        if tokens[1].bracket == '(':
            func = tokens[0].data
            if func in inline_functions:
                return (inline_functions[func]([x.data for x in tokens[1]]), '__int.0')
            if func in high_functions:
                return (high_functions[func](tokens[1]), func + '.retval')
            raise SyntaxError(f'Unable to call function {func}!')
    #Handle assignment:
    if tokens[1].data == '=':
        if tokens[0].ttype in ('int', 'chr', 'str'):
            raise SyntaxError(f'Unable to use literal "{tokens[0].data}" as variable!')
        if isinstance(tokens[0], TokenList):
            raise SyntaxError(f'Unable to use bracketed expression {tokens[0].data} as variable!')
        newasm, reg = evaluate_expr(tokens[2:-1], registers)
        asm += newasm
        func = inline_functions['setval']
        asm += func([tokens[0].data, reg])
        data_sect.add_var(tokens[0].data)
        return (asm, '__reg.0')
    while position + 1 < len(tokens):
        item = tokens[position]
        if isinstance(item, Token) and item.data not in data_sect.vars:
            if not item.data.startswith('__int.') and item.data.startswith('__func'):
                raise SyntaxError(f'Undefined variable: \"{item.data}\"')
        opr = tokens[position + 1]
        if item.ttype != 'sym' and not isinstance(item, TokenList):
            raise SyntaxError(f'Unexpected token: "{item.data}"')
        if isinstance(opr, TokenList):
            #Function call:
            if opr.bracket == '(':
                func = item.data
                if func in inline_functions:
                    raise SyntaxError(f'Function {func} has no return value!')
                if func in high_functions:
                    func_asm, retreg = high_functions[func](opr)
                    asm += func_asm
                    final_asm, final_reg = evaluate_expr(expression[:position] + [retreg] + expression[position+1:])
                    return (asm + final_asm, final_reg)
                raise SyntaxError(f'Unable to call function {func}!')
        if opr.ttype != 'opr':
            raise SyntaxError(f'Invalid operator: {opr.data}')
        oprio = prio[opr.data]
        if oprio > cprio:
            citem = item
            cprio = oprio
            copr = opr
            position += 2
        else:
            fname = ''
            if copr.data in operator_functions:
                fname = operator_functions[copr.data]
            else:
                raise SyntaxError(f'Unsupported operator: "{copr.data}"')
            func = inline_functions[fname]
            reg = data_sect.add_register(registers)
            registers += 1
            #Handle brackets:
            if isinstance(citem, TokenList):
                newasm, reg1 = evaluate_expr(citem, registers)
                registers = int(reg1[6:]) + 1
                asm += newasm
                citem = Token(reg1)
            if isinstance(item, TokenList):
                newasm, reg1 = evaluate_expr(item, registers)
                registers = int(reg1[6:]) + 1
                asm += newasm
                item = Token(reg1)            
            asm += func([reg, citem.data, item.data])
            tokens[position - 2] = Token(reg)
            tokens.pop(-1)
            for x in range(2):
                tokens.pop(position - 1)
            final_asm, final_reg = evaluate_expr(tokens, registers)
            return (asm + final_asm, final_reg)
    raise SyntaxError("What did you do?!?!?!?!")
