PYTHON ?= python
.PHONY: setup data train evaluate test app report slides all
setup:
	$(PYTHON) -m pip install -r requirements.txt
data:
	$(PYTHON) data/generate_dataset.py
train:
	$(PYTHON) -m src.model.train
evaluate:
	$(PYTHON) -m scripts.benchmark
test:
	$(PYTHON) -m pytest --cov=src.pipeline --cov=src.model --cov=src.routing --cov-branch --cov-fail-under=90 --cov-report=json:results/coverage.json --junitxml=results/junit.xml
app:
	$(PYTHON) -m streamlit run src/ui/app.py
report:
	$(PYTHON) -m scripts.build_documents
slides:
	$(PYTHON) -m scripts.build_slides
all: train evaluate test report slides
