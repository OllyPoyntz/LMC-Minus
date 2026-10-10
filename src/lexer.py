'''Adaptable lexer designed for curly bracket languages.'''
from .preprocess import definitions
#List of acceptable bracket characters:
brackets = ('(', ')', '[', ']', '{', '}')
#Dictionary of corresponding closing brackets:
closing = {'(':')', '[':']', '{':'}'}
#Quote characters:
quotes = ('\'', '\"')
#Escape sequences:
escape = {'n':'\n', 't':'\t','\"':'\"', '\'':'\'', '\\':'\\', '0':'\0'}
#Operators:
operators = ('+', '-', '*',  '/', '%', '**', '<<', '>>',  '=', '==', '!=', '!', '>', '<', '>=', '<=', '@', '+=', '-=', '*=', '/=', '%=', '&', '&&', '|', '||')
#The six primary types of token:
tokentypes = ('opr',  'brc', 'str', 'chr', 'int', 'sym')

def is_valid_symbol(sym) -> bool:
    '''Determines if a string is allowed for use as a variable/function name.'''
    letters = [ord(x) for x in range(ord('a'), ord('z')+1)] + [ord(x) for x in range(ord('A'), ord('Z')+1)]
    numbers = [ord(x) for x in range(ord('0'), ord('9')+1)]
    punctuation = ('_', '.')
    for char in sym:
        if char not in letters and char not in numbers and char not in punctuation:
            raise SyntaxError(f'Symbol "{sym}" is not permissible; you may only use letters, numbers, underscores, and full stops.')
class Token:
    '''Class representing a token of code.
    Has six types: operator, bracket, string, character, integer, symbol.'''
    data = ''
    ttype = ''
    def __init__(self, string):
        self.data = string
        count = 0
        while self.data in definitions:
            self.data = definitions[self.data]
            count += 1
            if count >= 256:
                raise SyntaxError('Infinite definition loop detected!')
        if isinstance(string, Token):
            self.data = string.data
            self.ttype = string.ttype
        elif string in brackets:
            #Bracket (should be unused, but added for contingency).
            self.ttype = 'brc'
        elif string in operators:
            #Operator:
            self.ttype = 'opr'
        elif string[0] in quotes:
            #Character literals use single quotes - e.g '0'.
            #String literals use double quotes - e.g "0".
            #This is standard practice in C and other languages with separate character and string types.
            if string[0] == '\'':
                self.ttype = 'chr'
                self.data = string[1]
            else:
                self.ttype = 'str'
                self.data = string[1:-1]
        elif string.isnumeric():
            #Integer literal:
            self.ttype = 'int'
        else:
            #Generic 'symbol' type. Often a variable, function, or assembly mneumonic (where applicable).
            self.ttype = 'sym'
    def __eq__(self, other):
        if self.ttype == other:
            return True
        if hasattr(other, '__hash__'):
            if hash(other) == hash(self):
                return True
        return False
    def __hash__(self):
        return hash(self.ttype + self.data)
    def __repr__(self):
        return f'Token<{self.ttype}>("{self.data.__repr__()[1:-1]}")'
class TokenList:
    '''A list of tokens. Self-explanatory.'''
    tokens = []
    bracket = ''
    data = None
    ttype = None
    def __init__(self, bracket):
        self.bracket = bracket
        self.tokens = []
        self.i = 0
    #Limited list functionality is supported: standard indexing, append, and pop operations.
    def append(self, item):
        '''Adds an item to the token list.'''
        self.tokens.append(item)
    def pop(self, index):
        '''Pops an item from the list.'''
        return self.tokens.pop(index)
    def __setitem__(self, index, item):
        self.tokens[index] = item
    def __getitem__(self, index):
        return self.tokens[index]
    def __iter__(self):
        self.i = 0
        return self
    def __len__(self):
        return len(self.tokens)
    def __next__(self):
        if self.i < len(self.tokens):
            x = self.i
            self.i += 1
            return self.tokens[x]
        raise StopIteration
    def __repr__(self):
        return f'TokenList({self.tokens})'
def raise_error(line, msg):
    '''Raises an error.'''
    raise SyntaxError(f'Error at line {line}: {msg}')
def tokenise(code) -> list:
    '''Converts a string of code into a list of tokens.'''
    #Stack of brackets:
    bracketstack = []
    #Stack of TokenLists for handling bracketed expressions.
    tokenstack = []
    #Tokens in the current expression:
    ctokens = []
    #The variable 'tokens' gets manipulated so that tokens are added to the top list
    #on the token stack above.
    tokens = ctokens
    line = 1
    position = -1
    cstring = ''
    cchar = ''
    quote = False
    comment = False
    while position + 1 < len(code):
        position += 1
        cchar = code[position]
        
        #Newlines:
        if cchar == '\n':
            line += 1
            comment = False
            if not quote:
                continue
        #Comments:
        if position + 1 < len(code):
            if not cstring and not quote and cchar + code[position+1] == '//':
                comment = True
        if comment:
            continue
        #Currently parsing a string:
        if quote:
            if cchar in quotes:
                cstring += cchar
                quote = False
                tokens.append(Token(cstring))
                cstring = ''
            elif cchar == '\\':
                esc = code[position+1]
                if esc in escape:
                    position += 1
                    cstring += escape[esc]
                else:
                    raise_error(line, f'Invalid escape sequence:\\{esc}')

            else:
                cstring += cchar
            continue
        #Operators:
        if cchar in operators:
            if cstring:
                tokens.append(Token(cstring))
                cstring = ''
            #Check that the next character isn't part of a compound operator:
            if (position + 1 < len(code)) and (cchar + code[position+1]) in operators:
                tokens.append(Token(cchar + code[position+1]))
                position += 1
            else:
                tokens.append(Token(cchar))
            continue
        #Brackets:
        if cchar in brackets:
            if cstring:
                tokens.append(Token(cstring))
                cstring = ''
            #Check if it is an opening or closing brackets:
            opening = cchar in closing
            if opening:
                #Add another TokenList to the stack:
                tokenstack.append(TokenList(cchar))
                tokens = tokenstack[-1]
                bracketstack.append(cchar)
            else:
                if len(bracketstack) == 0:
                    raise_error(line, f'Unmatched bracket: "{cchar}"')
                if closing[bracketstack[-1]] != cchar:
                    raise_error(line, f'Closing bracket {cchar} does not match opening bracket.')
                else:
                    bracketstack.pop(-1)
                    tlist = tokenstack.pop(-1)
                    if len(tokenstack) > 0:
                        tokens = tokenstack[-1]
                    else:
                        tokens = ctokens
                    tokens.append(tlist)
            continue
        #String literals:
        if cchar in quotes:
            if cstring:
                tokens.append(Token(cstring))
            cstring = cchar
            quote = True
            continue
        #Spaces and commas:
        if cchar in (' ', ',', '\t'):
            if cstring:
                tokens.append(Token(cstring))
            cstring = ''
            continue
        #Semicolons indicate the end of a line of code:
        if cchar == ';':
            if cstring:
                tokens.append(Token(cstring))
            cstring = ''
            tokens.append(Token(cchar))
            continue
        #Everything else:
        cstring += cchar
    if len(cstring) > 0:
        tokens.append(Token(cstring))
    if len(bracketstack) > 0:
        raise_error(line, 'Unmatched bracket(s).')
    return ctokens
