.PHONY: test
hello:
	echo "Hello World"
test:
	@echo "Runing Pytest"
	pytest -vs --clean-alluredir --alluredir tmp/allure_results
report:
	allure serve tmp/allure_results
diagram:
	pyreverse -o pdf -p AgentBasedSHM src/abm_chans
	mv *AgentBasedSHM.pdf img/diagram/.
	ls img/diagram
update-dependencies:
	conda list -e > requirements.txt
	conda env export > freeze.yml
install-dependencies:
	conda install matplotlib pandas scipy numpy seaborn networkx geopandas rasterio pyyaml rioxarray geocube cf_xarray metpy openpyxl pint-pandas cartopy netCDF4
	pip install agentpy prettytable rasterstats pyet dataclasses-json
install-tests:
	conda install pytest
	pip install allure-pytest
install-plot:
	pip install pygam
install-jupyter:
	conda install nb_conda
	conda install jupyterlab_execute_time
	conda install jupyterlab-lsp
	conda install -c conda-forge python-lsp-server
	pip install jupyterlab-citation-manager
	# pip install jupyterlab_darkside_ui
install-mkdocs:
	conda install mkdocs
	conda install jinja2=3.0.3
	pip install mkdocs-material
	pip install mkdocstrings\[python\]
	pip install mkdocs-bibtex
	pip install mkdocs-macros-plugin
	pip install mkdocs-jupyter
	pip install mkdocs-callouts
