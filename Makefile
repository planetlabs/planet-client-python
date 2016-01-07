GH_PAGES_SOURCES = planet docs Makefile

check:
	py.test tests
	flake8 planet tests

pex:
	pex .  -o dist/planet -m planet.scripts:cli

html-docs:
	python docs/source/generate.py
	$(MAKE) -C docs clean html

docs-zip: html-docs
	cp -a docs/build/html planet-docs
	zip -m -r dist/planet-docs.zip planet-docs

gh-docs:
	git checkout gh-pages
	rm -rf *
	git checkout master $(GH_PAGES_SOURCES)
	git reset HEAD
	make html-docs
	mv -fv docs/build/html/* ./
	rm -rf $(GH_PAGES_SOURCES)
	git add -A
	git commit -m "gh-pages for `git log master -1 --oneline`"

release:
	@[ $(TAG) ] || exit 1
	@[ $(BODY) ] || exit 1
	@sed -i -e "s/__version__ =.*/__version__ = '$(TAG)'/" planet/__init__.py
	git --no-pager diff
	@echo 'About to tag/release $(TAG)'
	@echo -n 'Does the above diff look right (Y/N)? :'
	@read PROCEED
	@[ $PROCEED != 'Y' ] && exit 0
	@echo 'OK!'
	git commit -m "release version $(TAG)" .
	git push origin
	make DRAFT=false release-gh

release-gh: check pex docs-zip
	TAG="$(TAG)" BODY="$(BODY)" DRAFT="$(DRAFT)" ./gh-release

