'''Parsing of high-level functions and code.'''
import json
import os
import sys
from .lexer import Token, TokenList, tokenise
from .lowlink import inline_functions, next_call, InlineFunction
from .data import data_sect
from .expr import evaluate_expr, high_functions
from .optimise import optimise
from .preprocess import preprocess, definitions
keywords = ['return', 'if', 'while', 'array']
with open(os.path.dirname(__file__)+'/stdlib_functions.json', 'r', encoding='utf-8') as f:
    data = f.read()
stdlib_functions = json.loads(data)
def symbolise(tokens, name):
    '''Ensures symbols are properly made static.'''
    for x in tokens:
        if x.data is None:
            x.tokens = symbolise(x.tokens, name);
            continue
        conditions = (x.data, x.ttype == 'sym', x.data not in keywords, x.data != ';', not x.data.startswith('__'), x.data not in inline_functions, x.data not in high_functions)
        if all(conditions):
            x.data = '__func.' + name + '.' + x.data
    return tokens
def generate_asm(code, name, definition = False, debug = False):
    '''Generates assembly for arbitrary high-level code.'''
    asm = ''
    if definition:
        if debug:
            sys.stderr.write(f'Generating assembly for function "{high_functions[name]}"\n')
        asm = name + ' LDA __int.0\n'
    position = -1
    registers = 0
    cexpr = []
    while position + 1 < len(code):
        position += 1
        ctoken = code[position]
        #If statement:
        if ctoken.data == 'if':
            if position + 2 >= len(code):
                raise SyntaxError('Incomplete if statement.')
            condition = code[position+1]
            branch_code = code[position+2]
            eval_asm, out_reg = evaluate_expr(condition)
            asm += eval_asm
            #Actually perform the if statement:
            callid = next_call()
            asm += f'LDA {out_reg}\n'
            asm += f'BRZ __endif_{callid}\n'
            asm += generate_asm(branch_code, name)
            asm += f'__endif_{callid} LDA __int.0\n'
            position += 2
            cexpr = []
            continue
        #While loop:
        if ctoken.data == 'while':
            if position + 2 >= len(code):
                raise SyntaxError('Incomplete while loop.')
            condition = code[position+1]
            branch_code = code[position+2]
            eval_asm, out_reg = evaluate_expr(condition)
            #Start of while loop:
            callid = next_call()
            asm += f'__while_start_{callid} LDA __int.0\n'
            asm += eval_asm
            asm += f'LDA {out_reg}\n'
            asm += f'BRZ __while_end_{callid}\n'
            asm += generate_asm(branch_code, name)
            asm += f'BRA __while_start_{callid}\n'
            asm += f'__while_end_{callid} LDA __int.0\n'
            cexpr = []
            position += 2
            continue
        #Array statement:
        if ctoken.data == 'array':
            if position + 2 >= len(code):
                raise SyntaxError('Incomplete array declaration.')
            if code[position+1].ttype != 'sym':
                raise SyntaxError(f'Invalid array name "{code[position+1].ttype}"')
            arrname = code[position+1].data
            if not isinstance(code[position+2], TokenList) or len(code[position + 2]) < 1:
                raise SyntaxError(f'Array "{arrname}" needs bracketed declaration of length - e.g "array {arrname}[16]"')
            if code[position+2][0] != 'int':
                raise SyntaxError(f'Declaration of array "{arrname}" requires a positive integer length.')
            size = int(code[position+2][0].data)
            if size <= 0:
                raise SyntaxError(f'Array "{arrname}" is not declared with a positive integer length.')
            newasm = data_sect.add_array(arrname, size)
            asm += newasm
            position += 3
            cexpr = []
            continue
        if ctoken.data == ';':
            if len(cexpr) == 0: continue
            #Return:
            if cexpr[0].data == 'return':
                if len(cexpr) >= 2:
                    newasm, reg = evaluate_expr(cexpr[1:])
                    asm += newasm
                else:
                    reg = '__int.0\n'
                asm += f'LDA {reg}\n'
                asm += f'STA {name}.retval\n'
                asm += f'BRA {name}.retbranch\n'
                continue
            if cexpr[0].ttype == 'sym' and isinstance(cexpr[1], TokenList) and cexpr[1].bracket == '(':
                #Function call:
                fname = cexpr[0].data
                args = cexpr[1]
                registers = 0
                if fname.startswith('__func.'):
                    errormsg = f'Unknown function: "{''.join(fname.split('.')[2:])}".'
                    #Additional context if it's a stdlib function:
                    if fname.split('.')[2] in stdlib_functions:
                        errormsg += ' Did you remember to include the correct headers?'
                    raise SyntaxError(errormsg)
                if fname in inline_functions:
                    regs = []
                    for x in args:
                        if x.ttype == 'str':
                            strname = data_sect.add_string_literal(x.data)
                            asm += f'LDA load_{strname}\n'
                            asm += 'SUB __base_load\n'
                            asm += f'STA __reg.{registers}\n'
                            x.data = f'__reg.{registers}'
                            registers += 1
                        newasm, reg = evaluate_expr(x.data, registers)
                        asm += newasm
                        regs.append(reg)
                    asm += inline_functions[fname]([x for x in regs])
                elif fname in high_functions:
                    regs = []
                    for x in args:
                        if x.ttype == 'str':
                            strname = data_sect.add_string_literal(x.data)
                            asm += f'LDA load_{strname}\n'
                            asm += 'SUB __base_load\n'
                            asm += f'STA __reg.{registers}\n'
                            x.data = f'__reg.{registers}'
                            registers += 1
                        newasm, reg = evaluate_expr(x.data, registers)
                        asm += newasm
                        regs.append(reg)
                    asm += high_functions[fname]([Token(x) for x in regs])
            else:
                asm += evaluate_expr(cexpr)[0]
            cexpr = []
            continue
        cexpr.append(ctoken)
    if definition:
        asm += name + '.retbranch BRA __int.0\n'
        #Ensure we exit properly from main():
        if name == 'main':
            asm += inline_functions['exit'](['main.retval'])
    data_sect.add_integers(asm)
    return asm
class HighLevelFunction:
    '''Class representing a high-level (non-inline) function.'''
    name = ''
    params = []
    code = []
    is_ptr = {}
    def __init__(self, fname, params, fcode, debug=False):
        self.name = fname
        self.params = list(params)
        self.params = symbolise(self.params, self.name)
        self.code = list(fcode)
        self.code = symbolise(self.code, self.name)
        self.debug = debug
        if fname not in high_functions:
            high_functions[fname] = self
        else:
            raise SyntaxError(f'Multiple definitions of function {fname}')
        self.called = False
    def __repr__(self):
        output = f'{self.name}('
        length = len('__func.'+self.name+'.')
        for x in range(len(self.params)):
            output += self.params[x].data[length:]
            if (x+1) != len(self.params):
                output += ', '
        output += ')'
        return output
    def generate_asm(self):
        '''Generates assembly that defines the function.'''
        for x in self.params:
            data_sect.add_var(x.data)
        data_sect.add_var(self.name + '.retval')
        return generate_asm(self.code, self.name, True, self.debug)
    def call(self, args):
        '''Generates assembly for a function call.'''
        if len(self.params) != len(args):
            raise SyntaxError(f'Function {self} takes {len(self.params)} arguments but {len(args)} were given.')
        if not self.called:
            self.called = True
            asm = self.generate_asm()
            data_sect.data += asm
        callid = next_call()
        asm = ''
        #Load args into the function's parameters:
        for i in range(len(args)):
            if args[i].ttype == 'int':
                args[i].data = f'__int.{args[i].data}'
                args[i].ttype = 'sym'
            elif args[i].ttype == 'chr':
                args[i].data = f'__int.{ord(args[i].data)}'
                args[i].ttype = 'sym'
            asm += f'LDA {args[i].data}\n'
            asm += f'STA {self.params[i].data}\n'
        #Load the return branch:
        asm += f'LDA retbranch_{callid}\n'
        asm += f'STA {self.name}.retbranch\n'
        asm += f'BRA {self.name}\n'
        asm += f'retbranch_{callid} BRA retpoint_{callid}\n'
        asm += f'retpoint_{callid} LDA __int.0\n'
        data_sect.add_integers(asm)
        return asm
    def __call__(self, args):
        return self.call(args)
def compile_code(code, filename, do_optimise = True, debug=False):
    '''Main interface for the compilation of code.'''
    splitcode = preprocess(code, filename, debug=debug)
    code = ''
    for x in splitcode:
        code += x + '\n'
    asm= ''
    tokens = tokenise(code)
    
    position = -1
    while position + 1 < len(tokens):
        position += 1
        ctoken = tokens[position]
        #Inline function:
        if ctoken.data == 'asm':
            try:
                fname, params, fcode = tokens[position+1:position+4]
            except ValueError:
                raise SyntaxError('Incomplete inline function declaration.')
            func = InlineFunction(fname, params, fcode)
            inline_functions[fname.data] = func
        #High-level function:
        if ctoken.data == 'func':
            try:
                fname, params, fcode = tokens[position+1:position+4]
            except ValueError:
                raise SyntaxError('Incomplete function declaration.')
            func = HighLevelFunction(fname.data, params, fcode, debug=debug)
    print([f for f in high_functions] + [f for f in definitions])
    if 'main' not in high_functions:
        raise SyntaxError('Function \'main\' needs to be defined as an entry point!')
    #Fake call main() to generate relevant code:
    high_functions['main']([])
    asm = '_start BRA main\n' + data_sect.data
    asm += '__stack_pos DAT 1\n'
    if do_optimise:
        asm = optimise(asm, debug)
    return asm
