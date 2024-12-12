---
title: contributing
---
<!-- markdownlint-disable -->
As an open source project, ABSESpy welcomes contributions of many forms, and from beginners to experts. If you are curious or just want to see what is happening, we post our development session agendas and development session notes on [discussions](https://github.com/ABSESpy/ABSESpy/discussions)
In no particular order, examples include:

- Code patches
- Bug reports and patch reviews
- New features
- Documentation improvements
- Tutorials

**submit a contribution**  

- Find or create something you want to work on
- Fork the ABSESpy repository
- Clone your repository to your computer
- Create a new branch for your work `git checkout -b YOUR_BRANCH`
- Recommend run `git config pull.rebase true` to prevent messy merge commit
- Install the environment `poetry install`
- Edit your change such as code or docs. Save
- Add your change file or added file by git `git add FILE_NAME`
- Commit your changes with a message `git commit -m "Fix: DESCRIBE"`. The message should follow [conventional commit](https://www.conventionalcommits.org/en/v1.0.0/)
- Make sure that your submission works with a few of the examples in the examples repository. And if implementing a new feature, include some documentation in docs folder.
- Check if your change passes the `pre-commit`. 
- Push your change to your fork repository `git push origin BRANCH_NAME`
- Create a pull request and describe your change.

## How to start

Maybe you are confused about where to start. It's OK! We provide some suggestions depend on your experience:

### You are a modeller

You already know how to build ABM model and want to build your own model by ABSESpy. You want to improve that and contribute your idea as an example. Awesome!
Firstly you should get some tools and their knowledge. The code is based on `python` and manage the version by `git`.
After that, talk to us about what you want to change, and open a small PR. Or update the [example](https://github.com/ABSESpy/ABSESpy/tree/master/examples)

### You are a developer

Great! You have the basics of open-source software development, but not much modelling experience.
In this case, learn something about ABM (agent based model). And you can run a model in [mesa-example](https://mesa.readthedocs.io/latest/tutorials/visualization_tutorial.html) which is a important ABM python package.

### You are both

Wonderful! You can just start your work and read our workflow to prevent some error. 

## Test and code standard

If you're changing previous features, please make sure of the following:

- Your changes pass the current tests.
- Your changes pass our style standards.
- Your changes don't break the models or your changes include updated models.
- Additional features or rewrites of current features are accompanied by tests.
- New features are demonstrated in a model, so folks can understand more easily.
- New docs or changing docs better in `md` format and follow the `markdownlint`

To ensure your code exclude the style error, we recommend `mypy` .

```shell
pip install mypy
mypy test.py
```

This process will return the style error if it existed.

To ensure your code will pass our style standards, we recommend `black`.

```shell
pip install black
black test.py
```

Black need a file named "`pyproject.toml`" which had included in our project.

>You also can use `ruff`.

Test and manage your environment and dependencies by `tox`. It is a auto-testing tool to simplify multi-environments testing and dependency management. You can create, manage and run different testing environments by `tox.ini`.

```shell
pip instal tox
tox -e your_environment
```

## License

The license of this project is located in [[ABSESpy/docs/home/license|license]]. By submitting a contribution to this project, you are agreeing that your contribution will be released under the terms of this license.

## Maintainers

Some notes useful for ABSESpy maintainers.

### Releases

To create a new release, follow these steps:
1. Ensure all pull requests (PRs) have a clear title and are labeled with at least one label.
2. Navigate to the [Release](https://github.com/ABSESpy/ABSESpy/releases) section in the Github UI and click the *Draft a new release* button.
3. Use the _Generate release notes_ button to automatically create release notes. Review them carefully for accuracy, and update labels and edit PR titles if necessary (step 1).
4. Write a _Highlights_ section summarizing the most important features or changes in this release.
5. Copy the release notes and save them by clicking the grey _Save draft_ button.
6. Open a new PR to update the version number.
7. Once this PR is merged, return to the _Releases_ section and publish the draft release.
8. Finally, after release, open a new PR to update the version number.

## Special Thanks

[clone your repository]: https://help.github.com/articles/cloning-a-repository/
[create a pull request]: https://help.github.com/articles/creating-a-pull-request/
[license]: https://github.com/projectmesa/mesa/blob/main/LICENSE
[pre-commit]: https://github.com/pre-commit/pre-commit