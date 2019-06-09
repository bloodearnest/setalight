PYDIR = venv
VENV = $(PYDIR)/.done
PYBIN = $(PYDIR)/bin
SET ?= test_sets/set1.eml
DIR ?= build


.PHONY: build
build: dist/index.html $(SET)
	python3 src/build.py $(SET) $(DIR)

dist/inline.html: dist/main.js dist/index.html dist/main.css
	npx inline-source --compress --root dist dist/index.html > $@

dist/index.html: dist/main.js

dist/main.js: src/*.js webpack.config.js package.json
	npx webpack

clean:
	rm -f dist/main.js dist/inline.html

full-clean: clean
	rm -rf venv node_modules

.PHONY: test
test: $(VENV)
	PYTHONPATH=src/ $(PYBIN)/pytest tests/

$(VENV): Makefile requirements.txt
	virtualenv -p python3 venv
	$(PYBIN)/pip install -r requirements.txt
	touch venv/.done

system-dependencies:
	sudo apt install -y python3 poppler-utils virtualenv
