# external_updater developer documentation

The documentation on this page is for developers of `external_updater`. If
you're looking for user documentation, see the [README.md].

## Development environment

Development of `external_updater` requires a full checkout of the main branch of
AOSP, and a lunched target (any target). See [Get started with Android
Development] for a guide on setting up an AOSP build environment.

Note: This project uses Python 3.11. You may find [pyenv] helpful for installing
and managing multiple versions of Python.

Not all the Python tools used here are available in AOSP. For managing those, we
recommend using a Python virtual environment (venv). To create one:

```bash
$ python -m venv venv
```

To install the necessary Python dependencies:

```bash
$ source venv/bin/activate
$ python -m pip install mypy pylint pytest
```

`source venv/bin/activate` will make the venv active for the current shell. You
can exit the venv with `deactivate`.

[README.md]: ../README.md
[pyenv]: https://github.com/pyenv/pyenv
[Get started with Android Development]: https://source.android.com/docs/setup

## Development tasks

Assuming you're using a venv as described in the section above, you must
activate the venv before running any of the commands below, and the venv should
be selected as the Python runtime for your editor. You only need to do this once
per shell session.

Run the type checker and linter with `make lint`.

Run the tests with `make test`.

Run all of the above with `make check` or just `make`.
