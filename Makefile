PYTHONS    ?= "python2.7 pypy"

venv-%:
	test -d venv-${*} || virtualenv -p ${*} venv-${*}
	venv-${*}/bin/pip install -Ur requirements.txt
	touch venv-${*}/bin/activate

devbuild-%: venv-%
	venv-${*}/bin/python setup.py install

test-%: devbuild-%
	cd tests && ../venv-${*}/bin/py.test -q -r fEsxXw --strict

coverage-%: devbuild-%
	cd tests && ../venv-${*}/bin/py.test --cov-report term-missing --cov ../venv-${*}/lib/${*}/site-packages/iktomi

test2: test-python2.7
test3: test-python3.5
test: test2 test3
coverage: coverage-python2.7

#docs-%: devbuild
#	cd doc && make SPHINXBUILD=../venv/bin/sphinx-build $*
