'''Preprocessor for including files.'''
import os
import sys
rootdir = os.path.dirname(os.path.dirname(__file__))
include_dir = rootdir + '/include'
definitions = {}
preprocess_stack = []
def preprocess(code, filename, included_files = set(), debug=False):
    '''Handles include statements recursively.'''
    #Split the code for processing line by line:
    splitcode = code.split('\n')
    x = -1
    filename = os.path.realpath(filename)
    #Not using a for loop here because the length of the split code could change.
    #Popping from the middle of a list is inefficient, but it won't make a difference for small lists.
    while x + 1 < len(splitcode):
        line = splitcode[x]
        #Strip spaces from the line:
        oldline = line + ' '
        while oldline == line:
            oldline = line
            line = line.strip(' ').strip('\t')
        #Handle #endif directives:
        if line.startswith('#endif'):
            if preprocess_stack:
                preprocess_stack.pop(-1)
            splitcode.pop(x)
            continue
        #Handle #else directives:
        if line.startswith('#else'):
            #Just pop a boolean from the stack and invert it:
            if preprocess_stack:
                preprocess_stack.append(not preprocess_stack.pop(-1))
            splitcode.pop(x)
            continue
        #Lines are not processed if there is a false directive on the stack:
        if not all(preprocess_stack):
            splitcode.pop(x)
            continue
        #Handle #ifdef directives:
        if line.startswith('#ifdef'):
            splitline = line.split(' ')
            if len(splitline) == 2:
                macro = splitline[1]
                preprocess_stack.append(macro in definitions)
            splitcode.pop(x)
            continue
        #Handle #ifndef directives:
        if line.startswith('#ifndef'):
            splitline = line.split(' ')
            if len(splitline) == 2:
                macro = splitline[0]
                preprocess_stack.append(macro not in definitions)
            splitcode.pop(x)
            continue
        #Handle #define directives by adding them to a dictionary:
        if line.startswith('#define'):
            splitline = line.split(' ')
            if len(splitline) == 3:
                token1 = splitline[1]
                token2 = splitline[2]
                definitions[token1] = token2
                if debug:
                    sys.stderr.write(f'Macro "{token1}" defined as "{token2}".\n')
            splitcode.pop(x)
            continue
        #Handle #include directives by preprocessing the file and inserting the processed code.
        #Files are only included once; no need for header guards or 
        if line.startswith('#include '):
            splitline = line.split(' ')
            if len(splitline) == 2:
                file = splitline[1]
                if file.startswith('<') and file.endswith('>'):
                    target_file = include_dir + '/' + file[1:-1]
                else:
                    target_file = os.path.dirname(filename) + '/' + file[1:-1]
                target_file = os.path.realpath(target_file)
                try:
                    if os.path.realpath(target_file) not in included_files:
                        included_files.add(target_file)
                        with open(target_file, 'r', encoding='utf-8') as f:
                            data = f.read()
                            if debug:
                                sys.stderr.write(f'Included file {target_file}\n')
                            splitcode = splitcode[:x] + preprocess(data, target_file, included_files, debug) + splitcode[x+1:]
                except (FileNotFoundError, PermissionError):
                    sys.stderr.write(f'Unable to open {target_file} for reading!\n')
                    sys.exit(1)
        x += 1
    return splitcode
