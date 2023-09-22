VERSION := $(shell cat transip_dns/__init__.py | grep version | cut -d '"' -f2)
PACKAGE_NAME := transip-dns
MODULE_NAME := transip_dns
PIP_ENV := .venv

SOURCE_FILES := $(wildcard transip_dns/*) $(wildcard tests/*) 

all: dev dist

force: touch all

touch:
	touch transip_dns/*
	touch tests/*

dev: venv
venv: $(PIP_ENV)/bin/activate

$(PIP_ENV)/bin/activate:
	PIPENV_VENV_IN_PROJECT=1 pipenv install --dev --python 3.6

dist: venv test sdist bdist_wheel requirements
sdist: dist/$(PACKAGE_NAME)-$(VERSION).tar.gz
bdist_wheel: dist/$(MODULE_NAME)-$(VERSION)-py3-none-any.whl

test: cov.xml linting requirements
cov.xml: venv $(SOURCE_FILES)
	pipenv run pytest --cov=transip_dns --cov-report xml:cov.xml --cov-report term tests
	rm -rf .pytest_cache

linting:
	pipenv run flake8
	pipenv run pydocstyle
	pipenv run black . --check --exclude "(docs|\.vscode|local)" 	

dist/$(PACKAGE_NAME)-$(VERSION).tar.gz: test $(SOURCE_FILES)
	pipenv run python setup.py sdist
	rm -rf	build $(MODULE_NAME).egg-info

dist/$(MODULE_NAME)-$(VERSION)-py3-none-any.whl: test $(SOURCE_FILES)
	pipenv run python setup.py bdist_wheel
	rm -rf	build $(MODULE_NAME).egg-info 

requirements: dev-requirements.txt requirements.txt
dev-requirements.txt requirements.txt: Pipfile.lock
	pipenv lock -r > requirements.txt
	pipenv lock -r --dev > dev-requirements.txt

prepare_changelog:
	echo [$(VERSION)] - $(shell date +"%Y-%m-%d") >next_changelog
	echo ____________________>>next_changelog
	git log --pretty="%h - %s (%an)" $$(git tag | tail -1)..HEAD >>next_changelog

build_changelog: prepare_changelog
	git checkout HEAD -- CHANGELOG.rst
	mv CHANGELOG.rst CHANGELOG.rst.bck 
	mv next_changelog CHANGELOG.rst
	cat CHANGELOG.rst.bck >> CHANGELOG.rst
	rm CHANGELOG.rst.bck
	# git commit -m "Release v$(VERSION)"; git push
	# git tag -a v$(VERSION) -m "Release $(VERSION)"; git push --tags

clean:
	rm -rf  \
		.eggs \
		.coverage* \
		coverage.xml \
		.pytest_cache \
		.tox \
		.venv \
		$(MODULE_NAME).egg-info \
		.coverage \
		__pycache__ \
		*/__pycache__ \
		cov.xml \
		build


.PHONY: prepare_changelog requirements linting clean dist sdist bdist_wheel dev force all touch