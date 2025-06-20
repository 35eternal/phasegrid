# Coverage.py configuration file

[run]
source = .
omit = 
    */tests/*
    */test_*
    */__pycache__/*
    */venv/*
    */env/*
    setup.py
    run_tests.py
    */migrations/*
    */.git/*
    */htmlcov/*
    */output/*
    */credentials/*

[report]
# Regexes for lines to exclude from consideration
exclude_lines =
    # Have to re-enable the standard pragma
    pragma: no cover

    # Don't complain about missing debug-only code:
    def __repr__
    if self\.debug

    # Don't complain if tests don't hit defensive assertion code:
    raise AssertionError
    raise NotImplementedError

    # Don't complain if non-runnable code isn't run:
    if 0:
    if __name__ == .__main__.:
    
    # Don't complain about type checking code
    if TYPE_CHECKING:

ignore_errors = True

[html]
directory = output/coverage_html

[xml]
output = output/coverage.xml