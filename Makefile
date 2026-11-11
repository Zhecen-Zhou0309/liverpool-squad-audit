PYTHON ?= python3

.PHONY: setup data report test reproduce app

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install -r requirements.lock

data:
	$(PYTHON) scripts/fetch_data.py --manifest reproducibility/baseline.json

report:
	$(PYTHON) scripts/report.py

test:
	$(PYTHON) -m unittest discover -s tests -v

reproduce:
	$(PYTHON) scripts/reproduce.py

app:
	.venv/bin/python -m streamlit run app.py
