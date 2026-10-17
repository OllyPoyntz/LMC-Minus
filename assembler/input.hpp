// The input function is complicated, so it has a separate file:
#pragma once
#include <iostream>
#include <string>

// String buffer:
std::wstring buffer;
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
	if (buffer.length() == 0) {
		std::getline(std::wcin, buffer);
		buffer += L"\n";
	}
	isnum = is_digital(buffer);
}
// Take the actual input:
int read_input() {
	if (buffer.length() == 0) {
		flush_stdin();
	}
	if (isnum) {
		int num = std::stoi(buffer);
		buffer.clear();
		return num;
	}
	else {
		int chr = buffer[0];
		buffer = buffer.substr(1, buffer.length() - 1);
		return chr;
	}
}


