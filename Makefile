run: venv
		$(VENV)/python3 src/main.py $(ARGS)

tests: venv
		$(VENV)/python3 src/test/run_tests.py

show-req: venv
		$(VENV)/pip3 freeze

freeze: venv
		$(VENV)/pip3 freeze > requirements.txt

include Makefile.venv
Makefile.venv:
	curl \
		-o Makefile.fetched \
		-L "https://github.com/sio/Makefile.venv/raw/v2020.08.14/Makefile.venv"
	echo "5afbcf51a82f629cd65ff23185acde90ebe4dec889ef80bbdc12562fbd0b2611 *Makefile.fetched" \
		| shasum -a 256 --check - \
		&& mv Makefile.fetched Makefile.venv
