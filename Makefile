#!make
-include .env

TENDERMINT_VERSION ?= 0.34.24
PYTHON_EXEC ?= python3.10
VENV ?= "${CURDIR}/.venv"
PLATFORM ?= linux_amd64

SHELL := /bin/bash

venv:
	[ -d $(VENV) ] || $(PYTHON_EXEC) -m venv $(VENV)
	source $(VENV)/bin/activate && pip install -U pip setuptools_scm setuptools wheel
	wget -qO- https://github.com/tendermint/tendermint/releases/download/v$(TENDERMINT_VERSION)/tendermint_$(TENDERMINT_VERSION)_$(PLATFORM).tar.gz | tar xvz -C $(VENV)/bin tendermint

update-venv:
	[ -d $(VENV) ] || $(MAKE) venv
	source $(VENV)/bin/activate && pip install -e .


