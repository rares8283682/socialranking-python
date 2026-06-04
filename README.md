# socialranking

Python tools for power relations, coalitional rankings, and social ranking solutions, based on an existing R implementation.

This project is currently in the early porting stage. The first goal is to reproduce the core R objects and the lexicographical excellence ranking method in Python.

## Installation

Install locally from this source folder in editable mode:

```bash
python -m pip install -e ".[dev]"
```

Editable mode means that changes made in `src/socialranking/` are immediately available without reinstalling the package.

PyPI installation is not available yet. It can be added later once the library has a stable first release.

## Quick Start

The public API is still being implemented. The intended usage will look like:

```python
from socialranking import PowerRelation

pr = PowerRelation.from_nested([
    [[1, 2]],
    [[1]],
    [[2]],
])
```

Later, once the first ranking method is implemented, usage should look like:

```python
from socialranking import PowerRelation, lexcel_ranking

pr = PowerRelation.from_string("12 > 1 > 2")
ranking = lexcel_ranking(pr)
print(ranking)
```

## Features

Planned first features:

- `PowerRelation`: represent ordered equivalence classes of coalitions.
- `SocialRanking`: represent final rankings of individual elements.
- `create_powerset`: generate coalitions from a set of elements.
- `lexcel_scores`: compute lexicographical excellence score vectors.
- `lexcel_ranking`: rank elements using lexicographical excellence.

## Project Structure

```text
Python Library EAI/
  pyproject.toml
  README.md
  src/
    socialranking/
      __init__.py
      power_relation.py
      social_ranking.py
      helpers.py
      rankings.py
  tests/
    test_helpers.py
    test_package_import.py
```

## Requirements

- Python 3.10 or newer
- `pytest` for development and testing

The runtime dependency list is currently empty. Additional packages such as `numpy` or `networkx` may be added later if they are useful for the port.

## Development Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the package locally with development tools:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## Testing

Tests are stored in `tests/`.

The goal of the test suite is to compare the Python implementation with the behavior and examples from the original R files.

## Documentation

Documentation is currently kept in project notes and LaTeX logs.

Future documentation may include:

- API reference
- examples
- mathematical background
- porting notes from the R implementation

## Contributing

This project is in an early research-porting stage. Contributions should focus on small, testable changes that reproduce behavior from the original R implementation.

Recommended workflow:

1. Open an issue or discussion describing the function or behavior to port.
2. Create a branch for the change.
3. Add or update tests using examples from the R implementation.
4. Open a pull request with a short explanation of what was ported and how it was tested.

A formal `CONTRIBUTING.md` file can be added once the project has more contributors.

## License

No license has been selected yet. A license should be chosen before publishing the package publicly.

## Acknowledgments

This project is based on an existing R implementation of social ranking and power relation functions, together with research material provided by collaborators.

## Citation

A citation entry can be added once the repository name, final package name, and publication location are fixed.
