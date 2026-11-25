.PHONY: run test

run:
	python main.py && python diff.py

test:
	pytest tests/ -v
