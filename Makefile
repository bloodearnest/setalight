PYDIR = venv
VENV = $(PYDIR)/.done
PYBIN = $(PYDIR)/bin

dist/test.html: ARGS ?= ~/Downloads/12th
dist/test.html: src/*.py dist/index.html dist/main.js
	python3 src/build.py $(ARGS) > $@

dist/index.html: dist/main.js src/index.html
	npx inline-source --compress --root dist src/index.html > dist/index.html

dist/main.js: src/main.js webpack.config.js
	npx webpack

dependencies:
	sudo apt install -y poppler-utils

$(VENV): Makefile requirements.txt
	virtualenv -p python3 venv
	$(PYBIN)/pip install -r requirements.txt
	touch venv/.done

test: $(VENV)
	PYTHONPATH=src/ $(PYBIN)/pytest tests/
