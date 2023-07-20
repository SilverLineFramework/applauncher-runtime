# by default will use settings.yaml, .appsettings.yaml and .secrets.yaml from config folder
run: venv
		$(VENV)/python3 src/main.py $(ARGS)

# how to specify a folder for settings inside config 
# 'make config/settings-folder' will use the settings files in this folder
# 'config/settings-folder' should have: settings.yaml, .appsettings.yaml and .secrets.yaml
config/%: venv
		ROOT_PATH_FOR_DYNACONF="$@" $(VENV)/python3 src/main.py $(ARGS)

# this shows how to specify specific settings files (inside conf folder)
tests: venv
		SETTINGS_FILE_FOR_DYNACONF="dev-1/settings.yaml;dev-1/.appsettings.yaml;dev-1/.secrets.yaml" $(VENV)/python3 src/test/run_tests.py

test-dockerio: venv
		$(VENV)/python3 src/test/test_scripts/test_docker_io.py

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