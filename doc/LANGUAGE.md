# Little Man C-Minus specification
This document describes the structure, syntax, and paradigms of Little Man C-Minus (LMC-). It is not an 'official' standard for the language by any means, but serves as a fairly complete guide for programmers.

# Preamble
This document assumes familiarity with the [Little Man Computer](https://en.wikipedia.org/wiki/Little_Man_Computer) and basic familiarity with the C programming language.

# Compiler 
The compiler is named `lmcc`, and is written in Python. It takes the filename of a LMC- file, and outputs assembly to `out.lmc`, or the file specified by `-o`. `-O` can be used to optimise the assembly, and `-D` can be used to print debug information.

Example usage:
```
./lmcc examples/helloworld.lms -o out.lmc -O
```

In this project, an assembler (and debugging version) is also included, which takes an assembly source file as an argument and is written in C++. Example:
```
./lmas out.lmc
./lmas_debug out.lmc
```

## Code optimisation
The compiler's optimisation algorithm works by sequentially executing the following tasks:
- Removing empty lines and trailing whitespace
- Removing useless load operations that are immediately followed by another.
- Removing some unreferenced symbols.
- Removing more redundant load operations.
- Removing redundant store operations.
- Removing almost all unreferenced symbols.

This reduces the assembly code size and causes minor speedup by removing unwanted assembly.
# Core principles
- The language shall compile perfectly to the assembly of the Little Man Computer.
- There is no strong typing system, only integer and pointer variables. Responsibility for distinguishing between the data types is delegated to the programmer.
- Everything must be stored before being used in any function call, save for integers and string literals. No recursion is permitted.
- Variables are static and local unless explicitly declared otherwise.
- The syntax should resemble C, minus the type system and other complexities, as much as possible.

# Basic syntax
```
// Comments are written using double slashes.
#include <stdio.lmh> // Header files still exist. They have extension .lmh.
// Like C, there needs to be a function called main():
func main() {
	a = 10;      // Variables have no strict typing. Statements end in semicolons.
	print(a);    // A print function for integers is implicitly defined.
	b = 5;
	b += 5;      // In place operation is permitted.
	c = a == b;  // Boolean variables are just integers, where 0 represents False and everything else represents True.
	str = "Test";// String literals are permitted, are null terminated, and are stored as a pointer to the first character. Pointer arithmetic still works.
	prints(str); // The lack of a strong typing system means separate print functions are required. Use flush() to print a newline.
	return c;    // Not necessary inside main() (or any procedure really), but this is how you return values.
}
```

# Low-level
The lowest level the compiler works with is Little Man Computer assembly. Some examples of the syntax used to make output assembly more readable are:
- Integer literals are written as `___int.<num> DAT <num>`
- String literals have a label with `__string_<hash>` and then a series of data statements.
- The first instruction is labeled `_start`, and is responsible for setting up a function call to `main()`.
- Functions are labeled with their name. Their static variables are defined as `__func.<name>.<var>`.
- All functions have a static `retval` and `retbranch`, used for returning values and control, respectively.
## Low-level library
Inline functions are mostly defined in files in [/lib](/lib). You can write your own as long as you conform to the (fairly obvious) syntax, and save the file with `.lma` as the extension. When they are called, the assembly code is fitted with the arguments and then pasted into the main output.
These functions can be called from user-defined functions, but do not have a return value.
Some of the core functions defined in here include:
- `print(num)` - Prints a number.
- `flush()` - Prints a newline character.
- `exit(code)` - Exits the program, with the assembler returning the specified exit code.

You can write inline assembly functions in your LMC- code directly, if you follow the syntax, but they must strictly be procedures. Values are passed by reference, making inline functions ideal for low-level memory operations.

An example of the syntax for inline functions is shown below, used to define the `flush()` function which prints a newline character:
```
asm flush() {
	LDA 10;
	OUT;
}
``` 
Functions starting with underscores are intended for internal use by the standard library and should not be used in your program code.
# Key concepts
This section explains how core concepts from other languages are handled in LMC-.
## Functions
To define a function, use the keyword `func`, then the function name, then any parameters in brackets, then the function's code inside curly brackets. Example:
```
func add_nums(a, b) {
    c = a + b;
    print(c);
}
```
Since the tokeniser only looks for the symbol `func` to find functions, you are free to annotate your functions with return types.

Arguments are always passed by value to high-level functions, and by reference to inline functions.

Values can be returned from a function by using the `return` keyword.

Function calls work just like every other high-level programming language, but your arguments cannot be compound expressions - they must be variables or literals.

## Data types
There is no strong typing system, but there are six distinct functional types of data, which each take up one mailbox.
### Integers
Integer types are the most common. They are unsigned - attempting to store a negative variable causes an error with the VM.

Positive integer literals are supported - e.g `a = 5`, and integers are stored with the label `__int.<value>`.

Operators available are addition (`+`), subtraction (`-`), multiplication (`*`), integer division (`/`), modulus (`%`), and in-place forms of all of these.

To print an integer, use the function `print(num)`.
#### Booleans
A value of `false` is represented by an integer value 0, and any other value represents `true`. You can use boolean literals if you include `<stdbool.lmh>`.

Booleans are returned by logical AND (`&`), logical OR (`|`), and equality comparison (`==` and `!=`).

To print a boolean, use the function `printb(bool)`, available in `<stdio.lmh>`.
#### Characters
Characters are also stored as integers, encoded using UTF-8. They support all of the operations integers do, and are not limited to ASCII.

To print a character, use `printc(char)` or `putchar(char)`.

### Pointers
Pointers are stored as integer values. They are added to internal values to produce load or store machine code operations by functions.

You can declare a pointer by using a pointer statement - e.g  `pointer foo(bar)` creates a pointer named  `foo` to the variable `bar`. 

To read or write from a pointer, use slicing - e.g `array[index] = 3;`. In place operations like `+=` are not supported for arrays, but you can still use syntax such as `array[index] = array[index] + 1;`

Pointer arithmetic with addition and subtraction is supported.

Null pointers are equivalent to `NULL` in `<stddef.lmh>`. Indexing them results in the program terminating, but passsing them to functions is permissible.

#### Arrays
To declare a static array, use the `array` keyword and specify how many mailboxes you wish to allocate - e.g `array buffer[16];`  The array is not garbage collected in any way, so use `memset(ptr, val, num)` to zero-initialise it if necessary. 

Arrays are stored and passed to functions as pointers.
#### Strings
Similar to C, strings are simply arrays of characters ending in a null byte, or mailbox in this case, with a pointer to the first character.

You can use string literals like `"Hello World!"`, but assigning it to a variable or using it in a function call returns a pointer the string literal in memory, not a new string, making it unsuitable for write-based operations. To fix this, declare a static array of the required length (remembering that the null terminator counts as a mailbox!), then `strcpy(dst, src)` the string to the newly allocated memory.

Dedicated functions for handling strings can be found in [string.lmh](/include/string.lmh). Non-ASCII characters are permitted.

A string can be outputted with `puts(string)` or `prints(string)`, available in `<stdio.lmh>`.

## Variables
Variables are all static, and always have a value of 0 when uninitialised.
### Global variables
Global variables can be used if defined inside of a function, and should be given a name that begins with two underscores - e.g `__foo = 10`.
The following global variables are defined on opening the program, and should not be modified at runtime:
- `__base_load`: Added to a pointer to make a load operation, or subtracted to generate a pointer.
- `__base_store`: Same as above, but for a store operation.
- `__ram_size`: The number of mailboxes available to the program.
- `__stack_pos`: The position of the memory allocation stack, relative to where `__stack_pos` is itself stored.

Note that if any of these variables are unreferenced, the optimiser will remove them.

Program code that accesses any of these should use the constants `BASE_LOAD`, `BASE_STORE`, `RAM_SIZE`, and `STACK_POS`, available in `<stddef.lmh>`.

## Flow control
`if` statements work identically to C, minus support for `else` and `else if`.

`for` loops are not supported, but you can replace them with `while` loops instead, which also work identically to C excluding `break` and `continue` statements.
## Entry point
The entry point of a program is always the function named `main()`. It must be defined or the compiler will throw an error, and cannot take parameters.

## Memory allocation
Dynamic memory allocation is done using [stack-based memory allocation](https://en.wikipedia.org/wiki/Stack-based_memory_allocation). There is a variable, `__stack_pos`, which uses its own position and value to manage the stack. To allocate memory, call `malloc(amount)` to allocate `amount` mailboxes on the stack and return a pointer to the allocated memory. To free it from the stack, call `free(amount)`.

You can also push and pop values using the functions `push(val)` and `pop()`. This is used by `stackprintf(format)` to efficiently print multiple values.

If the stack runs out of memory, it will simply loop around to the start and overwrite old memory.
## Preprocessing
Macros can be defined - if you use the directive `#define FOO BAR`, all instances of a token with data `FOO` will be replaced by `BAR`.

The preprocessor directives `#ifdef`, `#ifndef`, `#else`, and `#endif` all work approximately as they would in C.

### Header files
Header files have extension `.lmh`, and are included using `#include <name.lmh>` for standard library headers, or `#include "name.lmh"` for user-defined headers. The names generally match with equivalent C headers.

Currently defined header files are:
- [stdio.lmh](/include/stdio.lmh): Standard input/output. 
- [stdlib.lmh](/include/stdlib.lmh): Standard library functions, like `exit()` or `malloc(amount)`.
- [string.lmh](/include/string.lmh): String operations, like `strlen(string)` or `strcmp(string1, string2)`.
- [stack.lmh](/include/stack.lmh): Operations on the stack.
- [stdbool.lmh](/include/string.lmh): Macros for `true` and `false`.
- [stddef.lmh](/include/stddef.lmh): Macros defining constants such as `NULL` and `RAM_SIZE`.
- [math.lmh](/include/math.lmh): Mathematical functions.
- [all.lmh](/include/all.lmh): Includes all files. Doesn't cause code bloat, only longer compilation time, as assembly code for a function is only generated at the first call of the function.

The preprocessor will not include a file more than once when translating, and functions can call other functions from any point in the code, so there is no need to use `#ifndef` header guards.

## Standard library functions
A complete list of standard library functions is shown below:
### Implicit
- `print(num)`: Prints a number.
- `flush()`: Prints a newline
- `exit(code)`: Exits the program. The VM process should return the code to the operating system.

### Input/output
These functions are defined in `<stdio.lmh>`.
- `printc(char)`: Prints a character.
- `putchar(char)`: Same as above.
- `prints(string)`: Prints a string. Does not output newline characters unless they are in the string!
- `printb(bool)`: Prints a boolean value (0 = false, anything else = true).
- `input()`: Takes an integer input from the user. A prompt of `->` is automatically printed.
- `inputs(buffer)`: Takes a string input from the user, writing it to `buffer` and ignoring the trailing newline. Returns the length of the resulting string.
- `write(string, chars)`: Writes characters starting at the given pointer to standard output.
- `printf(format, args)`: Prints using a format string, which supports `%[bcds%]`. Variadic functions aren't possible, so an array is used instead.
- `stackprintf(format)`: Similar to `printf`, but it pops its arguments from the free store stack.
### Strings
These functions are defined in `<string.lmh>`.
- `memcpy(dst, src, num)`: Copies memory from `src` to `dst`. Essentially equivalent to its C counterpart.
- `memset(ptr, val, num)`: Direct memory manipulation. Again, essentially equivalent to C.
- `strlen(string)`: Determines the length of a null-terminated string, ignoring the null character. e.g strlen("Hello") would evaluate to 5.
- `strcmp(string1, string2)`: Compares two strings. Unlike C, it returns a boolean value reflecting whether or not the strings are equal, since negative numbers are not supported.
- `strcpy(dst, src)`: Copies a string from `src` to `dst`.
- `strncpy(dst, src, n)`: Copies at most `n` bytes from `src` to `dst`. Does not write a null character!
- `strcat(dst, src)`: Concatenates the string `src` to the end of `dst`.
- `strchr(string, chr)`: Finds the first occurrence of `chr` in the string, returning a pointer to it (or `NULL` if the character cannot be found).
- `getchar(string, index)`: Returns the character at the given string and index. Can also be used for general purpose memory reading.
- `setchar(string, index, char)`: Sets the character at the given index to `char`. Can also be used for general purpose memory writing.

### The Stack
These functions are defined in `<stack.lmh>`.
- `push(val)`: Pushes a value onto the stack.
- `pop()`: Pops a value from the stack and returns it.

### Miscellaneous
These functions are defined in `<stdlib.lmh>`.
- `malloc(amount)`: Allocates memory on the stack, returning a pointer to the allocated memory.
- `calloc(amount)`: Allocates memory on the stack and zero-initialises it using `memset(ptr, val, num)`.
- `free(amount)`: Frees stack-allocated memory by moving the stack pointer back.
- `atoi(string)`: Converts a string to an integer.
- `itoa(num, buffer)`: Converts an integer to a string, storing the result in `buffer`.
- `bsort(arr, length)`: Sorts an array of integers using a bubble sort algorithm. Requires quadratic time because `qsort()` would be too difficult to implement.
- `sort(arr, length)`: Defined by macro as the most efficient sorting algorithm in the implementation (currently `bsort`).
- `throw(msg)`: Prints an error message and then exits.
- `assert(val)`: Exits if `val` is equal to 0; i.e false.
### Mathematical
These functions are defined in `<math.lmh>`.
- `pow(a, b)`: Returns a raised to the power of b.
- `sqrt(num)`: Returns the square root of `num`, rounded down to the nearest integer. e.g `sqrt(5)` -> 2, `sqrt(16)` -> 4.
- `diff(a, b)`: Returns the absolute difference of a and b.
- `min(a, b)`: Returns the minimum value of a and b.
- `max(a, b)`: Returns the maximum value of a and b.
- `sum(arr, length)`: Returns the sum of values in an array.
- `mean(arr, length)`: Returns the mean of values in an array.
- `median(arr, length)`: Returns the median of values in an array. Does not require the array to be sorted.
- `mode(arr, length)`: Returns the mode of values in an array.

