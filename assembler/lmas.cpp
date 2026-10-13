#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>
#include "lmc.hpp"
namespace lmc {

    /* Split a string using the target character as a delimeter.
       (Similar to str.split() in Python.) */
    std::vector<std::string> split_str(const std::string instring, const char target_char) {
	    std::vector<std::string> outvector;
	    size_t pos = 0;
	    size_t oldpos = 0;
	    const size_t length = instring.length();
	    while (pos < length) {
		    if ((instring[pos] == target_char) || (pos == length - 1)) {
			    if ((instring[pos] != target_char) && (pos == length - 1)) {
				    pos++;
			    }
			    outvector.push_back(instring.substr(oldpos, pos-oldpos));
			    oldpos = pos+1;
		    }
		    pos++;
	    }
	    return outvector;
    }
    // Read code from a file and handle errors:
    std::string readcode(const std::string filename) {
	    std::ifstream infile(filename);
	    std::string outstr;
	    std::string buffer = "0";
	    if (!infile.is_open()) {
		    std::cerr << "Error: Unable to open file \"" << filename << "\" for reading!" << std::endl;
            std::exit(1);
	    }
	    while (getline(infile, buffer)) {
		    if (buffer.length() > 0) {
			    outstr += buffer + "\n";
		    }
	    }
	    infile.close();
	    return outstr;
    }
    // Used to raise syntax errors and terminate the program:
    void raise_error(std::string error, int linenum) {
	    std::cerr << "Error on line " << linenum << ":" << std::endl;
	    std::cerr << error << std::endl;
	    std::exit(1);
    }

    /* Decoding: returns the opcode that corresponds to a mneumonic.
       Even though the compiler's output is uppercase only,
       this function accepts anything as long as the case is consistent.
       
       Alternate mneumonics such as STO, COB, BR, etc. are not supported,
       although the non-standard OTC is since it makes things more interesting.
    */
    int get_opcode(const std::string mneumonic) {
	    if ((mneumonic == "HLT") || (mneumonic == "hlt")) {
		    return 0;
	    }
	    if ((mneumonic == "ADD") || (mneumonic == "add")) {
		    return 1;
	    }
	    if ((mneumonic == "SUB") || (mneumonic == "sub")) {
		    return 2;
	    }
	    if ((mneumonic == "STA") || (mneumonic == "sta")) {
		    return 3;
	    }
	    if ((mneumonic == "LDA") || (mneumonic == "lda")) {
		    return 5;
	    }
	    if ((mneumonic == "BRA") || (mneumonic == "bra")) {
		    return 6;
	    }
	    if ((mneumonic == "BRZ") || (mneumonic == "brz")) {
		    return 7;
	    }
	    if ((mneumonic == "BRP") || (mneumonic == "brp")) {
		    return 8;
	    }
	    if ((mneumonic == "INP") || (mneumonic == "inp") || (mneumonic == "OUT") || (mneumonic == "out") || (mneumonic == "OTC") || (mneumonic == "otc")) {
		    return 9;
	    }
	    std::string errormsg = "Unrecognised mneumonic: ";
	    errormsg += mneumonic;
	    raise_error(errormsg, 0);
	    return 0;
    }
    // Gets the operand from a mneumonic, if it is one where you needn't specify an operand in assembly.
    int get_operand(const std::string mneumonic) {
	    if ((mneumonic == "HLT") || (mneumonic == "hlt")) {
		    return 0;
	    }
	    if ((mneumonic == "INP") || (mneumonic == "inp")) {
		    return 1;
	    }
	    if ((mneumonic == "OUT") || (mneumonic == "out")) {
		    return 2;
	    }
	    if ((mneumonic == "OTC") || (mneumonic == "otc")) {
		    return 22;
	    }
	    return 0;
    }
    // Returns true if a mneumonic takes no operands, as above.
    bool is_single(const std::string mneumonic) {
	    return ((mneumonic == "HLT") || (mneumonic == "INP") || (mneumonic == "OUT") || (mneumonic == "OTC") || (mneumonic == "hlt") || (mneumonic == "inp") || (mneumonic == "out") || (mneumonic == "otc"));
    }
    /* Main translation function.
       Needs to return both a pointer to the machine code,
       and the length of the machine code, so a std::pair is used.
       Does not filter comments in the assembly.
    */
    std::pair<int*, size_t> assemble(const std::string code) {
	    std::vector<std::string> splitcode = split_str(code, '\n');
	    size_t ramsize = 100;
	    while (ramsize <= splitcode.size()) {
		    ramsize *= 10;
	    }
	    int* program = (int*)malloc(ramsize * sizeof(int));
        memset(program, 0, ramsize*sizeof(int));
	    std::unordered_map<std::string, size_t> labels;
	    size_t i = 0;
	    for (i = 0; i < splitcode.size(); i++) {
		    std::vector<std::string> splitline = split_str(splitcode[i], ' ');
		    if (splitline.size() == 3) {
			    std::string label = splitline[0];
			    if (labels.count(label) == 0) {
				    labels[label]  = i;
			    }
			    else {
				    raise_error("Duplicate label!", i+1);
			    }
		    }
		    else if (splitline.size() == 2) {
			    if (is_single(splitline[1])) {
				    std::string label = splitline[0];
				    if (labels.count(label) == 0) {
					    labels[label]  = i;
				    }
				    else {
					    raise_error("Duplicate label!", i+1);
				    }				
			    }
		    }
		    else if (splitline.size() > 3) {
			    raise_error("More than three symbols!", i+1);
		    }
	    }
	    for (i = 0; i < splitcode.size(); i++) {
		    std::vector<std::string> splitline = split_str(splitcode[i], ' ');
		    switch(splitline.size()) {
			    case 1:
				    {
					    std::string instr1 = splitline[0];
					    if (is_single(instr1)) {
						    program[i] = get_opcode(instr1) * ramsize + get_operand(instr1);
					    }
					    else {
						    raise_error("Instruction either does not exist or requires an operand.", i+1);
					    }
					    break;
				    }
			    case 2:
				    {
					    std::string item1 = splitline[0];
					    std::string item2 = splitline[1];
					    if (item1 == "DAT") {
						    program[i] = atoi(item2.c_str());
					    }
					    else if (is_single(item2)) {
						    program[i] = get_opcode(item2) * ramsize + get_operand(item2);
					    }
					    else if (labels.count(item2) > 0) {
						    int operand = labels[item2];
						    program[i] = get_opcode(item1) * ramsize + operand;
					    }
					    else {
						    raise_error("Unrecognised label: \"" + item2 + "\"", i+1);
					    }
					    break;
				    }
			    case 3:
				    {
					    std::string label = splitline[0];
					    std::string instr = splitline[1];
					    std::string target = splitline[2];
					    if (instr == "DAT") {
						    program[i] = atoi(target.c_str());
					    }
					    else if (labels.count(target) <= 0) {
						    raise_error("Unrecognised label: \"" + target + "\"", i+1);
					    }
					    else {
						    program[i] = get_opcode(instr) * ramsize + labels[target];
					    }
					    break;
				    }
		    }
	    }
	    return std::make_pair(program, ramsize);
    }
}
int main(int argc, char* argv[]) {
    // Necessary to print characters beyond 7-bit ASCII:
    setlocale(LC_ALL, "en_GB.utf8");
    // Only a single file should be specified:
	if (argc != 2) {
		std::cerr << "Usage: " << argv[0] << " <file>" << std::endl;
		return 1;
	}
    // Load the code from the file (error handling done by the function):
	const std::string code = lmc::readcode(argv[1]);
    // Translation from assembly to machine code:
	std::pair<int*, size_t> program = lmc::assemble(code);
    // Variable determining how many digits to use for each mailbox (3 in the original concept):
	const size_t digits = round(log10(program.second)) + 1;
    if (digits != 3) {
        std::cerr << "Executing with " << digits << " digits..." << std::endl;
    }
    /* Templates need to be known at compile time, so several precepts are present.
       If you manage to write an actual program that exceeds the limit,
       I wouldn't know whether to be impressed or concerned.
    */

	if (digits == 3) {
		lmc::LMC<3> computer;
		computer.load_program(program.first, program.second);
        // Note that free()ing the allocated memory is done by load_program().
		computer.execute();
	}
	if (digits == 4) {
		lmc::LMC<4> computer;
		computer.load_program(program.first, program.second);
		computer.execute();
	}
	if (digits == 5) {
		lmc::LMC<5> computer;
		computer.load_program(program.first, program.second);
		computer.execute();
	}
	if (digits == 6) {
		lmc::LMC<6> computer;
		computer.load_program(program.first, program.second);
		computer.execute();
	}
    std::cerr << "Unable to allocate more than 6 digits to an LMC program." << std::endl;
	return 1;
}