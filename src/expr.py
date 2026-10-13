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
#Returns (assembly, register in which to find result):
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
    #This token has a negative priority, ensuring that the function terminates:
    tokens.append(Token('@'))
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
        var = tokens[0]
        if var.data.startswith('__ptr'):
            func = inline_functions['_storeptr']
        else:
            func = inline_functions['_setval']
        
        asm += func([tokens[0].data, reg])
        data_sect.add_var(tokens[0].data)
        return (asm, '__reg.0')
    #Handle writing to arrays:
    if len(tokens) >= 4 and isinstance(tokens[1], TokenList) and tokens[2].data == '=' and tokens[0].ttype == 'sym':
        #Evaluate the index:
        index_expr = [x for x in tokens[1]]
        index_asm, index_reg = evaluate_expr(index_expr, registers)
        asm += index_asm
        reg = data_sect.add_register(registers)
        registers += 1
        
        #Temporary pointer variable:
        asm += f'''LDA {index_reg}
ADD {tokens[0].data}
STA __ptr
'''
        data_sect.add_var('__ptr')

        new_expr = [Token('__ptr')] + tokens[2:-1]
        final_asm, final_reg = evaluate_expr(new_expr, registers)
        return (asm + final_asm, final_reg)
    while position + 1 < len(tokens):
        item = tokens[position]
        if isinstance(item, Token) and item.data not in data_sect.vars:
            if not item.data.startswith('__int.') and item.data.startswith('__func'):
                raise SyntaxError(f'Undefined variable: \"{item.data}\"')
        opr = tokens[position + 1]
        if item.ttype != 'sym' and not isinstance(item, TokenList):
            raise SyntaxError(f'Unexpected token: "{item.data}"')
        #Operator is a TokenList - either a function call or a 
        if isinstance(opr, TokenList):
            #Function call:
            if opr.bracket == '(':
                func = item.data
                if func in inline_functions:
                    raise SyntaxError(f'Function {func} has no return value!')
                if func in high_functions:
                    func_asm = high_functions[func](opr)
                    retreg = func + '.retval'
                    asm += func_asm
                    final_asm, final_reg = evaluate_expr(tokens[:position] + [Token(retreg)] + tokens[position+2:-1])
                    return (asm + final_asm, final_reg)
                raise SyntaxError(f'Unable to call function {func}!')
            #Indexing:
            elif opr.bracket == '[':
                index_expr = [x for x in opr]
                index_asm, index_reg = evaluate_expr(index_expr, registers)
                reg = data_sect.add_register(registers)
                registers += 1
                #Call a function to get the index:
                fname = '_getindex'
                func = inline_functions[fname]
                new_asm = func([reg, item.data, index_reg])
                #Add the assembly and re-evaluate the expression:
                asm += index_asm + new_asm
                final_expr = tokens[:position] + [Token(reg)] + tokens[position+2:-1]
                final_asm, final_reg = evaluate_expr(final_expr)
                return (asm + final_asm, final_reg)
            else:
                raise SyntaxError("Curly brackets cannot follow a symbol in an expression.")
            
                
        if opr.ttype != 'opr':
            raise SyntaxError(f'Invalid operator: {opr.data}')
        #Get the operator's priority:
        oprio = prio[opr.data]
        #If the operator's priority is higher than the current priority, update  it:
        if oprio > cprio:
            citem = item
            cprio = oprio
            copr = opr
            position += 2
        else:
            #Lower priority operator; the operator takes effect.
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
