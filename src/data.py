'''Data section class.'''
from .lexer import Token, tokenise
class DataSection:
    '''Class which handles the creation of a data section for assembly.'''
    def __init__(self):
        #Actual data, as a string:
        self.data = 'section.data DAT 0\n'
        #Equivalent of a .text section:
        self.text = 'section.text DAT 0\n'
        #Set of existing variables so that we can avoid adding duplicates:
        self.vars = set()
        #Constants that are used by assembly functions (and sometimes high-level programs):
        self.data += '''__base_load LDA _start
__base_store STA _start
__ram_size ADD _start
'''
        #Add two registers to start with. We can always add more and remove extras with the optimisation tool.
        for x in range(2):
            self.add_var(f'__reg.{x}', 0)
    def add_var(self, varname, value=0):
        '''Adds a variable to the data section.'''
        if varname not in self.vars:
            self.data += varname + ' DAT ' + str(value) + '\n'
            self.vars.add(varname)
    def add_integers(self, code):
        '''Goes through assembly code looking for integers to add.'''
        #Note: Integers are stored with the label '__int.{value}'.
        code = code.replace('\n', ';\n')
        tokens = tokenise(code)
        for x in tokens:
            if not isinstance(x, Token):
                return
            if x.ttype == 'sym':
                if x.data.startswith('__int.'):
                    num = int(x.data[6:])
                    self.add_var(x.data, num)
    def add_string_literal(self, string) -> str:
        '''Adds a string literal to the data, returning the varname.'''
        #The first character in a string literal has the label "__string.{name}". The subsequent characters are unlabeled.
        #Like in C, strings are null-terminated.
        name = '__string.' + str(abs(hash(string)))
        if name in self.vars:
            return name
        charvalues = [ord(x) for x in string]
        charvalues.append(0)
        self.add_var(name, charvalues[0])
        for x in charvalues[1:]:
            self.data += 'DAT ' + str(x) + '\n'
        self.data += f'load_{name} LDA {name}\n'
        return name
    def add_register(self, num) -> str:
        '''Allocates a general purpose register for operations.'''
        self.add_var('__reg.' + str(num), 0)
        return '__reg.' + str(num)
    def add_array(self, name, length):
        '''Adds an array to the data section, returning the assembly needed to load the pointer.'''
        if f'__array_{name}' in self.vars:
            return ''
        self.vars.add(f'__array_{name}')
        self.add_var(name)
        arrayasm = f'__array_{name} '
        for _ in range(length):
            arrayasm += 'DAT 0\n'
        self.data += arrayasm
        self.data += f'__loadarray_{name} LDA __array_{name}\n'
        ptrasm = f'''LDA __loadarray_{name}
SUB __base_load
STA {name}
'''
        return ptrasm
    def add_function(self, txt):
        '''Adds a function to the text section.'''
        self.text += txt
    def __repr__(self):
        return 'DataSection:\n' + self.data + self.text
    def dumps(self):
        '''Return the data section in a textual format.'''
        return self.data + self.text
data_sect = DataSection()
data_sect.add_register(0)
