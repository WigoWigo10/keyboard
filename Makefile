test:
	python -m pytest --cov=directkeys --cov-report=html

lint:
	python -m ruff check .
	python -m ruff format --check .

format:
	python -m ruff check --fix .
	python -m ruff format .

build: tests src/directkeys pyproject.toml README.md CHANGES.md MANIFEST.in
	python ../docstring2markdown/docstring2markdown.py directkeys "https://github.com/WigoWigo10/keyboard/blob/master" > README.md
	find . \( -name "*.py" -o -name "*.sh" -o -name "* .md" \) -exec dos2unix {} \;
	python -m build && twine check dist/*

release:
	python make_release.py

clean:
	rm -rfv dist build coverage_html_report directkeys.egg-info