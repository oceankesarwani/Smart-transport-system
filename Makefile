# Makefile for Smart Public Transport Route & Crowd Prediction System

.PHONY: setup data train evaluate test app report slides all clean

PYTHON = python

setup:
	$(PYTHON) -m pip install -r requirements.txt

data:
	$(PYTHON) -m src.transport.data_gen

train:
	$(PYTHON) -m src.transport.model

evaluate:
	$(PYTHON) -m src.transport.evaluate

test:
	$(PYTHON) -m pytest -c pytest.ini --cov=src --cov-fail-under=80 tests/ -v

app:
	streamlit run app/streamlit_app.py

report:
	$(PYTHON) scripts/build_report_assets.py

slides:
	$(PYTHON) scripts/build_slides.py

all: data train evaluate test report slides
	@echo "All targets executed successfully."

clean:
	rm -rf __pycache__ src/transport/__pycache__ tests/__pycache__ .pytest_cache .coverage
