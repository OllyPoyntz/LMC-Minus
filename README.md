# Little Man C-Minus
Basic compiled language designed for the Little Man Computer.

# Introduction
This project was created because I wanted to attempt the daunting task of building a compiler from scratch. Since I have studied the [Little Man Computer](https://en.wikipedia.org/wiki/Little_Man_Computer)'s instruction set, I decided to use it as the target. The syntax of Little Man C-Minus (abbreviated LMC-) was designed to resemble C, but with a little more freedom due to the lack of a strong typing system, hence the name.

# Tools
The compiler can be used by executing [lmcc](/lmcc) with the name of an LMC- file (use the extension `.lms`) as an argument. Additional compiler flags include `-O` for optimisation and `-d` for debug mode.

The compiler outputs LMC assembly to the file specified by `-o`, or to `out.lmc` by default.

An assembler and VM for the resulting assembly is also included - `lmas` and `lmas_debug`. They are written in C++ and should be built by running `make all`.

# Syntax
An explanation of the language can be found in [LANGUAGE.md](/doc/LANGUAGE.md). A simple Hello World program is shown below as an example:
```
#include <stdio.lmh>
func main() {
	puts("Hello World!\n");
}
```

# Project structure
All directories in the project are listed below:
- [assembler](/assembler): C++ code implementing the assembler/VM.
- [doc](/doc): Documentation.
- [examples](/examples): Code snippets showing off the features of the langugage.
- [include](/include): LMC- header files which constitute the language's standard library.
- [lib](/lib): Lower-level functions written in a slight dialect of LMC assembly.
- [src](/src): Python source code for the actual compiler.

# License
The whole project, including the Python compiler, C++ assembler/VM, the LMC assembly library files, and the LMC- headers, is licensed under the permissive MIT license. This does not restrict the licenses you place on any code you write in LMC-, if you were to seriously attempt to write a project in this language for some cursed reason.





