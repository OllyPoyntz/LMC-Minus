'''Optimisation code.'''
import sys
def contains_symbol(splitcode, symbol) -> bool:
    '''Searches split code to see if it contains a given symbol.'''
    for x in splitcode:
        line = x + '\n'
        if line.count(symbol) > 0:
            if line[line.index(symbol) + len(symbol)] in (' ', '\n'):
                return True
    return False
def count_symbol(splitcode, symbol):
    '''Counts the number of occurrences of a symbol in split code.'''
    total = 0
    for x in splitcode:
        total += contains_symbol([x], symbol)
    return total
def optimise(asm, debug=False):
    '''Optimises assembly by removing unnecessary code.'''
    splitcode = asm.split('\n')
    #Remove empty lines:
    for x in splitcode:
        if len(x) < 2:
            splitcode.remove(x)
    initcodesize = len(splitcode)
    #Remove trailing whitespace:
    for x in range(len(splitcode)):
        while splitcode[x].endswith(' '):
            splitcode[x] = splitcode[x][:-1]
    #Remove redundant load operations.

    for _ in range(3):
        x = 0
        while x < len(splitcode):
            splitline = splitcode[x].split(' ')
            if splitline[0] == 'STA':
                label = splitline[1]
                splitline2 = splitcode[x+1].split(' ')
                if len(splitline2) == 2:
                    if splitline2[0] == 'LDA' and splitline2[1] == label:
                        splitcode.pop(x+1)
                        if debug:
                            sys.stderr.write('Removed redundant load operation.\n')
            x += 1
    #Remove unreferenced symbols:
    for _ in range(10):
        x = 0
        while x < len(splitcode):
            splitline = splitcode[x].split(' ')
            if len(splitline) >= 2:
                label = splitline[0]
                if label.startswith('__') or label.endswith('.retval') or label.endswith('.retbranch'):
                    if asm.count(label) == 1 and len(label) <= 36:
                        splitcode.pop(x)
                        if debug:
                            sys.stderr.write(f'Removed unnecessary symbol "{label}"\n')
            x += 1

    #Remove 'filler' load operations:
    for _ in range(3):
        x = 0
        while x < len(splitcode):
            splitline = splitcode[x].split(' ')
            if len(splitline) == 3 and splitline[1] == 'LDA':
                splitline2 = splitcode[x+1].split(' ')
                if len(splitline2) == 2 and splitline2[0] == 'LDA':
                    #Check that there are no operations reading the value of the redundant load operation:
                    readops = ['ADD', 'SUB', 'LDA', 'STA']
                    redundant = True
                    for y in readops:
                        if contains_symbol(splitcode, y + ' ' + splitline[0]):
                            redundant = False
                            break
                    if redundant and not splitline[0].startswith('ret'):
                        if debug:
                            sys.stderr.write(f'Removed redundant filler load operation {splitline[0]}\n')
                        newline = f'{splitline[0]} {splitline2[0]} {splitline2[1]}'
                        splitcode.pop(x)
                        splitcode[x] = newline
                       
            x += 1
    #Remove redundant store operations if the value is never read:
    x = 0
    while x < len(splitcode):
        splitline = splitcode[x].split(' ')
        if 'STA' in splitline:
            store_location = splitline[splitline.index('STA') + 1]
            if contains_symbol(splitcode, f'{store_location} DAT'):
                readops = ['ADD', 'SUB', 'LDA']
                redundant = True
                for y in readops:
                    if contains_symbol(splitcode, y + ' ' + store_location):
                        redundant = False
                        break
                if redundant:
                    splitcode.pop(x)
                    if debug:
                        sys.stderr.write(f'Removed redundant store operation on {store_location}\n')
        x += 1
    #Remove unreferenced symbols again:
    for _ in range(10):
        x = 0
        while x < len(splitcode):
            splitline = splitcode[x].split(' ')
            if len(splitline) >= 2:
                label = splitline[0]
                if len(label) <= 36 and label != label.upper() and count_symbol(splitcode, label) == 1:
                    splitcode.pop(x)
                    if debug:
                        sys.stderr.write(f'Removed unnecessary symbol "{label}"\n')
            x += 1
    endcodesize = len(splitcode)
    print(f'Optimisation: {initcodesize} -> {endcodesize}')
    newasm = ''
    for x in splitcode:
        newasm += x + '\n'
    return newasm
