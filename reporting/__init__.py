"""
reporting package: PDF regression-report generation for this project's
pytest suite (see reporting/pdf_report.py). Not a pytest plugin by itself -
the hooks that collect results live in the root conftest.py, which imports
build_pdf_report()/TestResult from here at session finish.
"""
