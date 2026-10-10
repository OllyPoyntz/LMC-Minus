COMPILER_FLAGS=-O3 -Ofast -flto -march=native -Os -s -Wall
lmas: assembler/lmas.cpp assembler/lmc.hpp
	g++ assembler/lmas.cpp -o lmas $(COMPILER_FLAGS)
lmas_debug: assembler/lmas.cpp assembler/lmas_debug.cpp assembler/lmc.hpp
	g++ assembler/lmas_debug.cpp -o lmas_debug $(COMPILER_FLAGS)
clean:
	rm -rf lmas lmas_debug clean.lmc __pycache__ src/__pycache__
test:
	for filename in examples/*.lms; do \
		echo $$filename ; \
		./lmcc $$filename -O ; \
	done
all: clean lmas lmas_debug
	echo "Built executables"

