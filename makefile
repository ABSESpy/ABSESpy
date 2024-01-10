setup:
	make install-tests
	make install-jupyter
	make setup-pre-commit
	make install-docs

# 安装必要的代码检查工具
# black: https://github.com/psf/black
# flake8: https://github.com/pycqa/flake8
# isort: https://github.com/PyCQA/isort
# nbstripout: https://github.com/kynan/nbstripout
# pydocstyle: https://github.com/PyCQA/pydocstyle
# pre-commit-hooks: https://github.com/pre-commit/pre-commit-hooks

setup-dependencies:
	poetry install

setup-pre-commit:
	poetry add --group dev flake8 isort nbstripout pydocstyle pre-commit-hooks interrogate sourcery mypy bandit black pylint

install-jupyter:
	poetry add ipykernel --group dev
	poetry add --group dev jupyterlab
	poetry add jupyterlab_execute_time --group dev

install-tests:
	poetry add hydra-core
	poetry add pytest allure-pytest --group dev
	poetry add pytest-cov --group dev
	poetry add pytest-clarity pytest-sugar --group dev

# https://timvink.github.io/mkdocs-git-authors-plugin/index.html
install-docs:
	poetry add --group docs mkdocs mkdocs-material
	poetry add --group docs mkdocs-git-revision-date-localized-plugin
	poetry add --group docs mkdocs-minify-plugin
	poetry add --group docs mkdocs-redirects
	poetry add --group docs mkdocs-awesome-pages-plugin
	poetry add --group docs mkdocs-git-authors-plugin
	poetry add --group docs mkdocstrings\[python\]
	poetry add --group docs mkdocs-bibtex
	poetry add --group docs mkdocs-macros-plugin
	poetry add --group docs mkdocs-jupyter
	poetry add --group docs mkdocs-callouts
	poetry add --group docs mkdocs-glightbox
	poetry add --group docs pymdown-extensions

test:
	poetry run pytest -vs --clean-alluredir --alluredir tmp/allure_results --cov=abses  --no-cov-on-fail

report:
	poetry run allure serve tmp/allure_results

jupyter:
	poetry run jupyter lab

diagram:
	pyreverse -o png -p ABSESpy abses
	mv *.png img/.
