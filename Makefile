
venv-%:
	test -d venv-${*} || virtualenv -p ${*} venv-${*}
	venv-${*}/bin/pip install -Ur requirements.txt
	touch venv-${*}/bin/activate

devbuild-%: venv-%
	#venv-${*}/bin/python setup.py install
	#venv-${*}/bin/pip uninstall iktomi
	venv-${*}/bin/pip install --upgrade .


test-%: name ?= tests
test-%: devbuild-%
	venv-${*}/bin/py.test $(name) -q -r fEsxXw --strict

coverage-%: devbuild-%
	venv-${*}/bin/py.test tests --cov-report=term-missing --cov=venv-${*}/lib/${*}/site-packages/iktomi | sed -e "s/^venv-${*}\\/lib\\/${*}\\/site-packages\\///"

test2: test-python2.7
test3: test-python3.5

test: test2 test3
coverage: coverage-python2.7

#docs-%: devbuild
#	cd doc && make SPHINXBUILD=../venv/bin/sphinx-build $*
