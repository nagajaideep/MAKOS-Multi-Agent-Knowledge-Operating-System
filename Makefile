PY ?= python

.PHONY: install data profile test

install:
	$(PY) -m pip install -r requirements.txt

# Stage 1: download BPI Challenge 2019 (~695 MB) and profile it
data:
	$(PY) data/scripts/download_bpi2019.py

profile:
	$(PY) data/scripts/profile_bpi2019.py

test:
	$(PY) -m pytest -q
