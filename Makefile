PYDIR = venv
VENV = $(PYDIR)/.done
PYBIN = $(PYDIR)/bin

.PHONY: build
build: 
	$(MAKE) dist/index.html
	python3 src/build.py $(DIR) > setlist.html

dist/index.html: dist/main.js src/index.html dist/main.css
	npx inline-source --compress --root dist src/index.html > dist/index.html

dist/main.js: src/main.js webpack.config.js package.json
	npx webpack

dependencies:
	sudo apt install -y python3 poppler-utils virtualenv

$(VENV): Makefile requirements.txt
	virtualenv -p python3 venv
	$(PYBIN)/pip install -r requirements.txt
	touch venv/.done

test: $(VENV)
	PYTHONPATH=src/ $(PYBIN)/pytest tests/
