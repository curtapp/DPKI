#!make
-include .env

TENDERMINT_VERSION ?= 0.34.24
PYTHON_EXEC ?= python3.10
NODE_VERSION ?= 16.17.0
VENV ?= "${CURDIR}/.venv"
PLATFORM ?= linux_amd64

SHELL := /bin/bash

venv:
	[ -d $(VENV) ] || $(PYTHON_EXEC) -m venv $(VENV)
	wget -qO- https://github.com/tendermint/tendermint/releases/download/v$(TENDERMINT_VERSION)/tendermint_$(TENDERMINT_VERSION)_$(PLATFORM).tar.gz | tar xvz -C $(VENV)/bin tendermint

update-venv:
	[ -d $(VENV) ] || $(MAKE) venv
	source $(VENV)/bin/activate && pip install -U pip setuptools_scm setuptools wheel
	source $(VENV)/bin/activate && pip install -e .

update-venv-front:
	$(MAKE) update-venv
	source $(VENV)/bin/activate && pip install -U nodeenv
	source $(VENV)/bin/activate && nodeenv -p -n $(NODE_VERSION)
	source $(VENV)/bin/activate && npm install -g npm
	source $(VENV)/bin/activate && npm install -g yarn

update-db:
	source $(VENV)/bin/activate && alembic upgrade head

create-db:
	source $(VENV)/bin/activate && pip install alembic
	mkdir -p .data
	$(MAKE) update-db