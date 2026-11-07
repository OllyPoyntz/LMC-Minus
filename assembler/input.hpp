// The input function is complicated, so it has a separate file:
#pragma once
#include <iostream>
#include <string>

namespace lmc {
	// String buffer:
	std::wstring ibuffer;
	// Boolean for if a numeric string has been read.
	bool isnum = false;

	// Determine if a wstring is entirely numeric:
	bool is_digital(const std::wstring instring) {
		if (instring.length() <= 1){
			return false;
		}
		for (size_t i = 0; i < instring.length(); i++) {
			wchar_t cchar = instring[i];
			if (((cchar < '0') || (cchar > '9')) && !(cchar == '\n')) {
				return false;
			}
		}
		return true;
	}
	// Repopulate the buffer with input:
	void flush_stdin() {
		if (ibuffer.length() == 0) {
			std::getline(std::wcin, ibuffer);
			ibuffer += L"\n";
		}
		isnum = is_digital(ibuffer);
	}
	// Take the actual input:
	int read_input() {
		if (ibuffer.length() == 0) {
			flush_stdin();
		}
		if (isnum) {
			int num = std::stoi(ibuffer);
			ibuffer.clear();
			return num;
		}
		else {
			int chr = ibuffer[0];
			ibuffer = ibuffer.substr(1, ibuffer.length() - 1);
			return chr;
		}
	}

}
