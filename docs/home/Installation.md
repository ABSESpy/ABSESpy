# Installation

## with pip <small>recommended</small> { #with-pip data-toc-label="with pip" }

`ABSESpy` is published as a [Python package] and can be installed with `pip` or your favorite PyPI package manager, ideally by using a [virtual environment]. Open up a terminal and install `ABSESpy` with:

=== "Latest"

    ``` sh
    pip install abses
    ```

This will automatically install compatible versions of [all dependencies].

<!-- We always strives to support the latest versions, so there's no need to install those packages separately. -->

!!! tip

    If you don't have prior experience with Python, we recommend reading
    [Using Python's pip to Manage Your Projects' Dependencies], which is a
    really good introduction on the mechanics of Python package management and
    helps you troubleshoot if you run into errors.

## From source with git

Material for MkDocs can be directly used from [GitHub] by cloning the
repository into a subfolder of your project root which might be useful if you
want to use the very latest version:

```sh
git clone https://github.com/SongshGeoLab/ABSESpy abses
```

Next, install the theme and its dependencies with:

```sh
pip install -e abses
```

<!-- Links -->
  [Python package]: https://pypi.org/project/mkdocs-material/
  [virtual environment]: https://realpython.com/what-is-pip/#using-pip-in-a-python-virtual-environment
  [Using Python's pip to Manage Your Projects' Dependencies]: https://realpython.com/what-is-pip/
  [all dependencies]: ../home/dependencies.md
  [GitHub]: https://github.com/SongshGeoLab/ABSESpy
