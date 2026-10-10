#pragma once
#include <iostream>
#include <cstdlib>
#include <cstring>
#include <cmath>
namespace lmc {

int zint(const char* string) {
    // Converts a string which may start with zeroes into an integer:
	size_t pos = 0;
	const size_t length = strlen(string);
	while (string[pos] == '0') {
		pos++;
		if (pos == length) {
			break;
		}
	}
	if (pos == length) {
		return 0;
	}
	return atoi(string + pos);
}
// Functions emulating the instructions:
void ADD(const int address, int* acc, int* ram, int* pc) {
	*acc += ram[address];
}
void SUB(const int address, int* acc, int* ram, int* pc) {
	*acc -= ram[address];
}
void LDA(const int address, int* acc, int* ram, int* pc) {
	*acc = ram[address];
}
void STA(const int address, int* acc, int* ram, int* pc) {
	ram[address] = *acc;
}
void BRA(const int address, int* acc, int* ram, int* pc) {
	*pc = address;
}
void BRP(const int address, int* acc, int* ram, int* pc) {
	if ((*acc) >= 0) {
		*pc = address;
	}
}
void BRZ(const int address, int* acc, int* ram, int* pc) {
	if ((*acc) == 0) {
		*pc = address;
	}
}
void INP(const int address, int* acc, int* ram, int* pc) {
	std::string buffer;
    std::cin >> buffer;
	*acc = zint(buffer.c_str());
}
void OUT(const int address, int* acc, int* ram, int* pc) {
	std::wcout << *acc << std::endl;
}
void OTC(const int address, int* acc, int* ram, int* pc) {
	wchar_t outchar = *acc;
	std::wcout << outchar;
}
void HLT(const int address, int* acc, int* ram, int* pc) {
	std::exit(*acc);
}

// Debugging printer:
#ifdef DEBUG
void print_ram(const int* ram, const size_t length) {
    for (size_t i = 0; i < length; i++) {
        int data = ram[i];
        std::cerr << data << ",";
    }
    std::cerr << std::endl;
}
void print_instruction(const int opcode, const int operand) {
    std::string mneumonic;
    switch (opcode) {
        case 0:
            std::cerr << "HLT" << std::endl;
            return;
        case 1:
            mneumonic = "ADD";
            break;
        case 2:
            mneumonic = "SUB";
            break;
        case 3:
            mneumonic = "STA";
            break;
        case 5:
            mneumonic = "LDA";
            break;
        case 6:
            mneumonic = "BRA";
            break;
        case 7:
            mneumonic = "BRZ";
            break;
        case 8:
            mneumonic = "BRP";
            break;
        case 9:
            if (operand == 1) {
                std::cerr << "INP" << std::endl;
                return;
            }
            if (operand == 2) {
                std::cerr << "OUT" << std::endl;
                return;
            }
            if (operand == 22) {
                std::cerr << "OTC" << std::endl;
                return;
            }
            return;
        default:
            return;
    }
    std::cerr << mneumonic << " " << operand << std::endl;
}
       
            
#endif

// Class which actually implements the Little Man Computer:
template <size_t digits>
class LMC {
	private:
	int ram[(size_t)round(pow(10, digits-1))];
	int pc = 0;
	int acc = 0;
	public:
	LMC<digits>() {
		memset(ram, 0, sizeof(int) * (size_t)round(pow(10, digits-1)));
	}
    // Loads the program into memory using memcpy():
	void load_program(int* arr, const size_t program_size) {
		memcpy(ram, arr, sizeof(int) * program_size);
        free(arr);
        // Debug information:
        #ifdef DEBUG
        print_ram(ram, (size_t)round(pow(10, digits-1)));
        #endif
	}
    // Initiates the execution.
	void execute() {
		for (;;) {
            // Fetch the instruction:
			int instruction = ram[pc];
            // Decode the instruction:
			int opcode = instruction / (size_t)round(pow(10, digits-1));
			int operand = instruction % (size_t)round(pow(10, digits-1));
            // Debug information:
            #ifdef DEBUG
            std::cerr << "PC: " << pc << "; ACC: " << acc << std::endl;
            print_instruction(opcode, operand);
            #endif
            // Increment the program counter:
			pc++;
            // Execute the instruction:
			switch(opcode) {
				case 0:
					HLT(operand, &acc, ram, &pc);
					break;
				case 1:
					ADD(operand, &acc, ram, &pc);
					break;
				case 2:
					SUB(operand, &acc, ram, &pc);
					break;
				case 3:
					STA(operand, &acc, ram, &pc);
					break;
				case 5:
					LDA(operand, &acc, ram, &pc);
					break;
				case 6:
					BRA(operand, &acc, ram, &pc);
					break;
				case 7:
					BRZ(operand, &acc, ram, &pc);
					break;
				case 8:
					BRP(operand, &acc, ram, &pc);
					break;
				case 9:
					switch (operand) {
						case 1:
							INP(operand, &acc, ram, &pc);
							break;
						case 2:
							OUT(operand, &acc, ram, &pc);
							break;
						case 22:
							OTC(operand, &acc, ram, &pc);
							break;
						default:
							std::cerr << "Unrecognised instruction: " << instruction << "!";
							HLT(operand, &acc, ram, &pc);
							break;
					}
					break;
				default:
					std::cerr << "Unrecognised instruction: " << instruction << "!";
					HLT(operand, &acc, ram, &pc);
					break;
			}
		}
	}
};

}
