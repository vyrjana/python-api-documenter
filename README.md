# python-api-documenter

A package for conveniently generating documentation of a Python API through introspection.


## Installing

Clone this repository and either a) copy the source files to your project or b) install this package locally:

`pip install -e .`


## Using

```python
import api_documenter


markdown_output: str = api_documenter.process(
    title="python-api-documenter",
    modules_to_document=[
        api_documenter,
    ],
    description="""
This is an optional description that is added between the main heading and the optional table of contents.
    """,
    table_of_contents=True,
    minimal_classes=[],
    objects_to_ignore=[],
    latex_pagebreak=False,
)
```

Below is an example of the output generated for the `api_documenter.process` function.

## **api_documenter.process**

Process one or more modules and generate API documentation through introspection.
Modules, classes, methods, and functions are processed using the `inspect` package.
Docstrings are validated against `inspect.Signature` objects to make sure that the docstrings are up-to-date in terms of identifiers, type annotations, and default values.
A Markdown document is generated and returned as a string.

```python
def process(title: str, modules_to_document: list, description: str = "", table_of_contents: bool = True, minimal_classes: list = [], objects_to_ignore: list = [], latex_pagebreak: bool = False) -> str:
```

_Parameters_
```python
title: str
```
- The main title/heading in the generated Markdown document.
This could be e.g. the name of the package.

```python
modules_to_document: list
```
- A list of modules to process and document.
Any classes, functions, or other modules in the listed modules will be processed.

```python
description: str = ""
```
- Optional text that is to be inserted between the main title/heading and the optional table of contents.

```python
table_of_contents: bool = True
```
- If true, then a table of contents with links will be generated.

```python
minimal_classes: list = []
```
- Any classes included in this list will only have their constructor documented.
Useful in cases where multiple subclasses could cause a lot of unnecessary duplicate entries when it would have been enough to just document the parent class.

```python
objects_to_ignore: list = []
```
- Any objects (e.g. modules, classes, methods, functions) included in this list will be ignored.

```python
latex_pagebreak: bool = False
```
- If true, then a LaTeX-style page break will be inserted before each module and after each class.
This could be useful if the intention is to convert the Markdown document into a PDF using Pandoc.

_Returns_
```python
str
```


## License

This project is licensed under the [MIT license](LICENSE).
