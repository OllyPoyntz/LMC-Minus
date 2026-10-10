'''Main interfaces for command line usage.'''
import argparse
import sys
from .functions import compile_code

def main():
    '''Main entry point.'''
    #Argument parser:
    parser = argparse.ArgumentParser()
    #Infile to take code from:
    parser.add_argument('file', type=str, help='Input code file')
    #Outfile to write code to:
    parser.add_argument('-o', '--outfile', type=str, help='Outfile to write assembly to (default out.lmc)')
    parser.add_argument('-O', '--optimise', help='Optimise the output by removing unnecessary statements.', action='store_true')
    #Debug mode:
    parser.add_argument('-d', '--debug', help='Prints debug information if applicable.', action='store_true')
    args = parser.parse_args(sys.argv[1:])

    source = args.file
    try:
        #Read the file:
        with open(source, 'r', encoding='utf-8') as f:
            code = ''
            buffer = '0'
            while buffer:
                buffer = f.read(4096)
                code += buffer
    except (PermissionError, FileNotFoundError):
        sys.stderr.write(f'Error: Unable to open file {source} for reading!\n')
        sys.exit(0)
    #Write the assembly to an outfile:
    outfile = args.outfile
    if outfile is None:
        outfile = 'out.lmc'
    #Stuff to avoid traceback:
    exceptiontype = None
    exceptiondata = None
    if not args.debug:
        sys.tracebacklimit = -1
    try:
        compiled_code = compile_code(code, source, args.optimise, args.debug)
    except Exception as e:
        if args.debug:
            raise(e)
        else:
            exceptiontype = type(e)
            exceptiondata = e
    if exceptiontype is not None:
        raise exceptiontype(exceptiondata)
    try:
        with open(outfile, 'w', encoding='utf-8') as f:
            f.write(compiled_code)
    except (PermissionError, FileNotFoundError):
        sys.stderr.write(f'Error: Unable to open file {outfile} for writing!\n')
        sys.exit(1)        
    sys.exit(0)
