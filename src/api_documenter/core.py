# MIT License
#
# Copyright (c) 2022 Ville Yrjänä
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import inspect
from inspect import Signature, Parameter
from re import match as regex_match
from string import ascii_letters
from typing import Any, List, Match, Optional, Tuple
from dataclasses import dataclass


ATTRIBUTES_HEADING: str = "Attributes"
PARAMETERS_HEADING: str = "Parameters"
RETURNS_HEADING: str = "Returns"


def _simplify_annotation(annotation):
    if annotation == Parameter.empty:
        return ""
    annotation = str(annotation)
    if annotation.startswith("<"):
        annotation = annotation[annotation.find("'") + 1 : -2]
    while "ForwardRef('" in annotation:
        annotation = annotation.replace("')", "", 1).replace("ForwardRef('", "", 1)
    stack = [[]]
    for char in annotation:
        if char in ascii_letters or char == "_":
            stack[-1].append(char)
        elif char == "[":
            stack.append(char)
            stack.append([])
        elif char == "]":
            substack = []
            while stack[-1] != "[":
                fragment = stack.pop()
                if fragment == ",":
                    substack.insert(0, ", ")
                else:
                    substack.insert(0, "".join(fragment))
            assert stack.pop() == "["
            stack.append(f'[{"".join(substack)}]')
        elif char == ",":
            stack.append(char)
            stack.append([])
        elif char == ".":
            stack[-1].clear()
        elif char == " ":
            pass
        else:
            raise Exception(f"Unexpected character: '{char}'")
    assert len(stack) <= 2, stack
    if len(stack) > 1:
        stack[0].append(stack.pop())
    annotation = "".join(stack[0])
    return annotation


@dataclass
class AttributeDocumentation:
    name: str
    annotation: str
    default: Any
    description: str

    def to_markdown(self) -> List[str]:
        # TODO: Implement
        return []


@dataclass
class ParameterDocumentation:
    name: str
    annotation: str
    default: Any
    description: str

    def to_markdown(self) -> List[str]:
        return [
            f"- `{self.name}`" + (f": {self.description}" if self.description else ""),
        ]


@dataclass
class FunctionDocumentation:
    name: str
    parameters: List[ParameterDocumentation]
    return_annotation: str
    description: str

    def to_markdown(self, module_name: str) -> List[str]:
        function_name: str = f"{module_name}.{self.name}"
        signature: str = f"def {self.name}("
        i: int
        param: ParameterDocumentation
        for i, param in enumerate(self.parameters):
            if i > 0:
                signature += ", "
            signature += param.name
            if param.annotation:
                signature += f": {param.annotation}"
            if param.default != Parameter.empty:
                if type(param.default) is str:
                    signature += f' = "{param.default}"'
                else:
                    signature += f" = {param.default}"
        if self.return_annotation:
            signature += f") -> {self.return_annotation}:"
        else:
            signature += "):"
        markdown: List[str] = [
            f"### **{function_name}**",
            f"\n{self.description}\n" if self.description else "\n",
            "```python",
            signature,
            "```",
            "",
        ]
        if self.parameters:
            markdown.append("\n_Parameters_\n")
            for param in self.parameters:
                markdown.extend(param.to_markdown())
            markdown.append("")
        if self.return_annotation:
            markdown.extend(
                [
                    "\n_Returns_\n",
                    "```python",
                    self.return_annotation,
                    "```",
                ]
            )
        return markdown


@dataclass
class MethodDocumentation:
    name: str
    parameters: List[ParameterDocumentation]
    return_annotation: str
    description: str

    def to_markdown(self, class_name: str) -> List[str]:
        method_name: str = f"{class_name}.{self.name}"
        signature: str = f"def {self.name}("
        i: int
        param: ParameterDocumentation
        for i, param in enumerate(self.parameters):
            if i > 0:
                signature += ", "
            signature += param.name
            if param.annotation:
                signature += f": {param.annotation}"
            if param.default != Parameter.empty:
                if type(param.default) is str:
                    signature += f' = "{param.default}"'
                else:
                    signature += f" = {param.default}"
        if self.return_annotation:
            signature += f") -> {self.return_annotation}:"
        else:
            signature += "):"
        markdown: List[str] = [
            f"#### **{method_name}**",
            f"\n{self.description}\n" if self.description else "\n",
            "```python",
            signature,
            "```",
            "",
        ]
        if self.parameters and not (
            len(self.parameters) == 1 and self.parameters[0].name in ["self", "Class"]
        ):
            markdown.append("\n_Parameters_\n")
            for param in self.parameters:
                if param.name == "self" or param.name == "Class":
                    continue
                markdown.extend(param.to_markdown())
            markdown.append("")
        if self.return_annotation:
            markdown.extend(
                [
                    "\n_Returns_",
                    "```python",
                    self.return_annotation,
                    "```\n",
                ]
            )
        return markdown


@dataclass
class ClassDocumentation:
    name: str
    parents: str
    parameters: List[ParameterDocumentation]
    methods: List[MethodDocumentation]
    description: str

    def to_markdown(self, module_name: str) -> List[str]:
        class_name: str = f"{module_name}.{self.name}"
        signature: str = f"class {self.name}"
        if self.parents:
            signature += f"({self.parents})"
        signature += ":"
        if self.parameters:
            param: ParameterDocumentation
            for param in self.parameters:
                if param.name == "self" or param.name == "Class":
                    continue
                signature += f"\n\t{param.name}"
                if param.annotation:
                    signature += f": {param.annotation}"
                if param.default != Parameter.empty:
                    if type(param.default) is str:
                        signature += f' = "{param.default}"'
                    else:
                        signature += f" = {param.default}"
        markdown: List[str] = [
            f"### **{class_name}**",
            f"\n{self.description}\n" if self.description else "",
            "```python",
            signature,
            "```",
        ]
        if self.parameters:
            markdown.append("\n_Constructor parameters_\n")
            for param in self.parameters:
                if param.name == "self" or param.name == "Class":
                    continue
                markdown.extend(param.to_markdown())
            markdown.append("")
        if self.methods:
            markdown.append("\n_Functions and methods_\n")
            met: MethodDocumentation
            for met in self.methods:
                markdown.extend(met.to_markdown(class_name))
        markdown.append("\n\\pagebreak\n")
        return markdown


@dataclass
class ModuleDocumentation:
    name: str
    classes: List[ClassDocumentation]
    functions: List[FunctionDocumentation]
    description: str

    def to_markdown(self) -> List[str]:
        markdown: List[str] = [
            "\n\\pagebreak\n",
            f"## **{self.name}**",
            self.description,
        ]
        for cls in self.classes:
            markdown.extend(cls.to_markdown(self.name))
        for func in self.functions:
            markdown.extend(func.to_markdown(self.name))
        return markdown


def _update_docstring_indentation(lines: List[str]) -> List[str]:
    line: str
    while lines:
        line = lines.pop(0)
        if line.strip() != "":
            lines.insert(0, line)
            break
    while lines:
        line = lines.pop()
        if line.strip() != "":
            lines.append(line)
            break
    if lines:
        indent_match: Optional[Match] = regex_match(r"^(\s+)", lines[0])
        if indent_match is not None:
            indent: str = indent_match.group(1)
            i: int
            for i in range(0, len(lines)):
                line = lines[i]
                if line.startswith(indent):
                    lines[i] = line[len(indent) :].rstrip()
    return lines


def _escape_docstring(lines: List[str]) -> List[str]:
    result: List[str] = lines[:]
    i: int
    line: str
    # Escape pipes (i.e., "|")
    in_table: bool = False
    for i, line in enumerate(result):
        if "|" not in line:
            in_table = False
            continue
        elif in_table:
            continue
        if line.strip().startswith("|") and line.strip().endswith("|"):
            in_table = True
            continue
        result[i] = line.replace("|", "\|")
    return result


def _extract_docstring_preamble(lines: List[str]) -> str:
    if not lines:
        return ""
    preamble: List[str] = []
    while lines:
        line: str = lines.pop(0)
        if line.strip() in [PARAMETERS_HEADING, RETURNS_HEADING]:
            lines.insert(0, line)
            break
        preamble.append(line)
    return "\n".join(_escape_docstring(preamble)).strip()


def _extract_name_annotation_default(line: str) -> Tuple[str, str, str]:
    name: str = ""
    annotation: str = ""
    default: str = ""
    if ":" in line:
        name, annotation = list(map(str.strip, line.split(":")))
        if "=" in annotation:
            annotation, default = list(map(str.strip, annotation.split("=")))
    elif "=" in line:
        name, default = list(map(str.strip, line.split("=")))
    else:
        name = line.strip()
    if (default.startswith('"') or default.startswith("'")) and (
        default.endswith('"') or default.endswith("'")
    ):
        default = default[1:-1]
    assert name != "", line
    return (
        name,
        annotation,
        default,
    )


def _extract_docstring_parameters(lines: List[str]) -> List[ParameterDocumentation]:
    if not lines:
        return []
    while lines:
        line: str = lines.pop(0)
        if line.strip() == PARAMETERS_HEADING:
            line = lines.pop(0).strip()
            assert line == "-" * len(PARAMETERS_HEADING), line
            break
        elif line.strip() == RETURNS_HEADING:
            lines.insert(0, line)
            return []
    parameters: List[ParameterDocumentation] = []
    while lines:
        line = lines.pop(0)
        if line.strip() == RETURNS_HEADING:
            lines.insert(0, line)
            break
        name: str
        annotation: str
        default: str
        name, annotation, default = _extract_name_annotation_default(line)
        description: List[str] = []
        while lines:
            line = lines.pop(0)
            if line.strip() == RETURNS_HEADING:
                lines.insert(0, line)
                break
            elif line.strip() == "":
                break
            description.append(line.strip())
        parameters.append(
            ParameterDocumentation(
                name,
                annotation,
                default,
                "\n".join(_escape_docstring(description)),
            )
        )
    return parameters


def _extract_docstring_returns(lines: List[str]) -> str:
    if not lines:
        return ""
    while lines:
        line: str = lines.pop(0).strip()
        if line == "":
            continue
        else:
            break
    assert line == RETURNS_HEADING, line
    line = lines.pop(0).strip()
    assert line == "-" * len(RETURNS_HEADING), line
    assert lines
    line = lines.pop(0).strip()
    assert line != ""
    return line


def _process_function(func) -> FunctionDocumentation:
    assert "TODO" not in (
        func.__doc__ or ""
    ), f"The docstring for the function {func} is incomplete!"
    docstring: List[str] = _update_docstring_indentation(
        (func.__doc__ or "").split("\n")
    )
    name: str = func.__name__
    description: str = _extract_docstring_preamble(docstring)
    signature: Signature = inspect.signature(func)
    signature_parameters: List[ParameterDocumentation] = []
    docstring_parameters: List[ParameterDocumentation] = _extract_docstring_parameters(
        docstring
    )
    key: str
    sig_param: Parameter
    default: Any
    if docstring_parameters:
        assert len(docstring_parameters) == len(signature.parameters), (
            func,
            name,
            len(docstring_parameters),
            len(signature.parameters),
        )
        assert set(list(map(lambda _: _.name, docstring_parameters))) == set(
            list(signature.parameters.keys())
        ), f"The docstring for the function {func} has a mismatch of parameters when compared to the function signature!"
        for key, sig_param in signature.parameters.items():
            assert (
                len(list(filter(lambda _: _.name == key, docstring_parameters))) == 1
            ), f"The docstring for the function {func} is missing parameter {key}!"
            doc_param: ParameterDocumentation = list(
                filter(lambda _: _.name == key, docstring_parameters)
            )[0]
            assert doc_param.annotation == (
                _simplify_annotation(sig_param.annotation)
            ), (
                func,
                doc_param.annotation,
                _simplify_annotation(sig_param.annotation),
            )
            default = sig_param.default if sig_param.default != Parameter.empty else ""
            assert doc_param.default == str(default), (
                func,
                doc_param.default,
                default,
            )
            doc_param.default = sig_param.default
            signature_parameters.append(doc_param)
    else:
        for key, sig_param in signature.parameters.items():
            signature_parameters.append(
                ParameterDocumentation(
                    key,
                    _simplify_annotation(sig_param.annotation),
                    sig_param.default,
                    "",
                )
            )
    return_annotation: str = _simplify_annotation(signature.return_annotation)
    assert _extract_docstring_returns(docstring) in [return_annotation, ""], func
    return FunctionDocumentation(
        name, signature_parameters, return_annotation, description
    )


def _process_method(met) -> MethodDocumentation:
    assert "TODO" not in (
        met.__doc__ or ""
    ), f"The docstring for the method {met} is incomplete!"
    docstring: List[str] = _update_docstring_indentation(
        (met.__doc__ or "").split("\n")
    )
    name: str = met.__name__
    description: str = _extract_docstring_preamble(docstring)
    signature: Signature = inspect.signature(met)
    signature_parameters: List[ParameterDocumentation] = []
    docstring_parameters: List[ParameterDocumentation] = _extract_docstring_parameters(
        docstring
    )
    key: str
    sig_param: Parameter
    default: Any
    if docstring_parameters:
        assert len(docstring_parameters) in [
            met,
            len(signature.parameters),  # Normal/class methods
            len(signature.parameters) - 1,  # Static methods
        ], (
            len(docstring_parameters),
            len(signature.parameters),
        )
        assert set(list(map(lambda _: _.name, docstring_parameters))).issubset(
            set(list(signature.parameters.keys()))
        ), f"The docstring for the method {met} has a mismatch of parameters when compared to the method signature!"
        for key, sig_param in signature.parameters.items():
            if key == "self" or key == "Class":
                signature_parameters.append(
                    ParameterDocumentation(key, "", Parameter.empty, "")
                )
                continue
            assert (
                len(list(filter(lambda _: _.name == key, docstring_parameters))) == 1
            ), f"The docstring for the method {met} is missing parameter {key}!"
            doc_param: ParameterDocumentation = list(
                filter(lambda _: _.name == key, docstring_parameters)
            )[0]
            assert doc_param.annotation == (
                _simplify_annotation(sig_param.annotation)
            ), (
                met,
                doc_param.annotation,
                _simplify_annotation(sig_param.annotation),
            )
            default = sig_param.default if sig_param.default != Parameter.empty else ""
            assert doc_param.default == str(default), (
                met,
                doc_param.default,
                default,
            )
            doc_param.default = sig_param.default
            signature_parameters.append(doc_param)
    else:
        for key, sig_param in signature.parameters.items():
            if key == "self" or key == "Class":
                signature_parameters.append(
                    ParameterDocumentation(key, "", Parameter.empty, "")
                )
            else:
                signature_parameters.append(
                    ParameterDocumentation(
                        key,
                        _simplify_annotation(sig_param.annotation),
                        sig_param.default,
                        "",
                    )
                )
    return_annotation: str = _simplify_annotation(signature.return_annotation)
    assert _extract_docstring_returns(docstring) in [return_annotation, ""], met
    return MethodDocumentation(
        name, signature_parameters, return_annotation, description
    )


def _process_class(
    cls, objects_to_ignore: list, minimal_classes: list
) -> ClassDocumentation:
    docstring: List[str] = _update_docstring_indentation(
        (cls.__doc__ or "").split("\n")
    )
    name: str = cls.__name__
    parents: str = ", ".join(list(map(lambda _: _.__name__, cls.__bases__)))
    description: str = _extract_docstring_preamble(docstring)
    signature: Signature = inspect.signature(cls.__init__)
    signature_parameters: List[ParameterDocumentation] = []
    key: str
    sig_param: Parameter
    default: Any
    if (cls.__doc__ or "") != "" and PARAMETERS_HEADING in (cls.__doc__ or ""):
        docstring_parameters: List[
            ParameterDocumentation
        ] = _extract_docstring_parameters(docstring)
        assert len(docstring_parameters) == len(signature.parameters) - 1, (
            cls,
            len(docstring_parameters),
            len(signature.parameters) - 1,
        )
        assert set(list(map(lambda _: _.name, docstring_parameters))).issubset(
            set(list(signature.parameters.keys()))
        ), f"The docstring for the class {cls} has a mismatch of parameters when compared to its constructor signature!"
        for key, sig_param in signature.parameters.items():
            if key == "self":
                signature_parameters.append(
                    ParameterDocumentation(key, "", Parameter.empty, "")
                )
                continue
            assert (
                len(list(filter(lambda _: _.name == key, docstring_parameters))) == 1
            ), f"The docstring for the class {cls} is missing parameter {key}!"
            doc_param: ParameterDocumentation = list(
                filter(lambda _: _.name == key, docstring_parameters)
            )[0]
            assert doc_param.annotation == (
                _simplify_annotation(sig_param.annotation)
            ), (
                cls,
                doc_param.annotation,
                _simplify_annotation(sig_param.annotation),
            )
            default = sig_param.default if sig_param.default != Parameter.empty else ""
            assert doc_param.default == str(default), (
                cls,
                doc_param.default,
                default,
            )
            doc_param.default = sig_param.default
            signature_parameters.append(doc_param)
    else:
        for key, sig_param in signature.parameters.items():
            signature_parameters.append(
                ParameterDocumentation(
                    key,
                    _simplify_annotation(sig_param.annotation),
                    sig_param.default,
                    "",
                )
            )
    methods: List[MethodDocumentation] = []
    if not issubclass(cls, Exception):
        for key, value in inspect.getmembers(cls):
            if key.startswith("_"):
                continue
            elif value in objects_to_ignore:
                continue
            if not (inspect.ismethod(value) or inspect.isfunction(value)):
                continue
            methods.append(_process_method(value))
        methods.sort(key=lambda _: _.name)
    return ClassDocumentation(
        name,
        parents,
        signature_parameters,
        methods if cls not in minimal_classes else [],
        description,
    )


def _process_module(
    mod, objects_to_ignore: list, minimal_classes: list
) -> ModuleDocumentation:
    docstring: List[str] = _update_docstring_indentation(
        (mod.__doc__ or "").split("\n")
    )
    name: str = mod.__name__
    description: str = _extract_docstring_preamble(docstring)
    classes: List[ClassDocumentation] = []
    functions: List[FunctionDocumentation] = []
    for key, value in inspect.getmembers(mod):
        if key.startswith("_"):
            continue
        elif value in objects_to_ignore:
            continue
        if inspect.isclass(value):
            classes.append(_process_class(value, objects_to_ignore, minimal_classes))
        elif inspect.isfunction(value):
            functions.append(_process_function(value))
    classes.sort(key=lambda _: _.name)
    functions.sort(key=lambda _: _.name)
    return ModuleDocumentation(name, classes, functions, description)


def _escape_link(link: str) -> str:
    link = link.replace(".", "")
    return link


def process_functions(
    functions_to_document: list,
    module_name: str,
    latex_pagebreak: bool = False,
) -> str:
    """
    TODO
    """
    function_documentations: List[FunctionDocumentation] = []
    for func in functions_to_document:
        assert inspect.isfunction(func), (
            func,
            type(func),
        )
        function_documentations.append(_process_function(func))
    function_documentations.sort(key=lambda _: _.name)
    markdown: List[str] = []
    doc: FunctionDocumentation
    for func in function_documentations:
        markdown.extend(doc.to_markdown(module_name))
    output: str = "\n".join(markdown)
    if not latex_pagebreak:
        output = output.replace("\\pagebreak", "")
    return output


def process_classes(
    classes_to_document: list,
    module_name: str,
    table_of_contents: bool = True,
    minimal_classes: list = [],
    objects_to_ignore: list = [],
    latex_pagebreak: bool = False,
) -> str:
    """
    Parameters
    ----------
    classes_to_document: list
        A list of classes to process and document.

    module_name: str
        The name of the parent module.

    table_of_contents: bool = True
        If true, then a table of contents with links will be generated.

    minimal_classes: list = []
        Any classes included in this list will only have their constructor documented.
        Useful in cases where multiple subclasses could cause a lot of unnecessary duplicate entries when it would have been enough to just document the parent class.

    objects_to_ignore: list = []
        Any objects (e.g., classes, methods, functions) included in this list will be ignored.

    latex_pagebreak: bool = False
        If true, then a LaTeX-style page break will be inserted before each module and after each class.
        This could be useful if the intention is to convert the Markdown document into a PDF using Pandoc.

    Returns
    -------
    str
    """
    class_documentations: List[ClassDocumentation] = []
    for Class in classes_to_document:
        assert inspect.isclass(Class), (
            Class,
            type(Class),
        )
        class_documentations.append(
            _process_class(Class, objects_to_ignore, minimal_classes)
        )
    class_documentations.sort(key=lambda _: _.name)
    markdown: List[str] = []
    contents: List[str] = []
    cls: ClassDocumentation
    for cls in class_documentations:
        link: str = _escape_link(f"{module_name.lower()}{cls.name.lower()}")
        contents.append(f"- [{cls.name}](#{link})")
        met: MethodDocumentation
        for met in cls.methods:
            link = _escape_link(
                f"{module_name.lower()}{cls.name.lower()}{met.name.lower()}"
            )
            contents.append(f"\t- [{met.name}](#{link})")
        markdown.extend(cls.to_markdown(module_name))
    if table_of_contents:
        markdown.insert(0, "\n")
        while contents:
            markdown.insert(0, contents.pop())
        markdown.insert(0, "**Table of Contents**\n")
    output: str = "\n".join(markdown)
    if not latex_pagebreak:
        output = output.replace("\\pagebreak", "")
    return output


def process(
    title: str,
    modules_to_document: list,
    description: str = "",
    table_of_contents: bool = True,
    minimal_classes: list = [],
    objects_to_ignore: list = [],
    latex_pagebreak: bool = False,
) -> str:
    """
    Process one or more modules and generate API documentation through introspection.
    Modules, classes, methods, and functions are processed using the `inspect` package.
    Docstrings are validated against `inspect.Signature` objects to make sure that the docstrings are up-to-date in terms of identifiers, type annotations, and default values.
    A Markdown document is generated and returned as a string.

    Parameters
    ----------
    title: str
        The main title/heading in the generated Markdown document.
        This could be e.g., the name of the package.

    modules_to_document: list
        A list of modules to process and document.
        Any classes, functions, or other modules in the listed modules will be processed.

    description: str = ""
        Optional text that is to be inserted between the main title/heading and the optional table of contents.

    table_of_contents: bool = True
        If true, then a table of contents with links will be generated.

    minimal_classes: list = []
        Any classes included in this list will only have their constructor documented.
        Useful in cases where multiple subclasses could cause a lot of unnecessary duplicate entries when it would have been enough to just document the parent class.

    objects_to_ignore: list = []
        Any objects (e.g., modules, classes, methods, functions) included in this list will be ignored.

    latex_pagebreak: bool = False
        If true, then a LaTeX-style page break will be inserted before each module and after each class.
        This could be useful if the intention is to convert the Markdown document into a PDF using Pandoc.

    Returns
    -------
    str
    """
    modules: List[ModuleDocumentation] = list(
        map(
            lambda _: _process_module(_, objects_to_ignore, minimal_classes),
            modules_to_document,
        )
    )
    modules.sort(key=lambda _: _.name)
    markdown: List[str] = []
    contents: List[str] = []
    mod: ModuleDocumentation
    for mod in modules:
        link: str = _escape_link(mod.name.lower())
        contents.append(f"- [{mod.name}](#{link})")
        cls: ClassDocumentation
        for cls in mod.classes:
            link = _escape_link(f"{mod.name.lower()}{cls.name.lower()}")
            contents.append(f"\t- [{cls.name}](#{link})")
            met: MethodDocumentation
            for met in cls.methods:
                link = _escape_link(
                    f"{mod.name.lower()}{cls.name.lower()}{met.name.lower()}"
                )
                contents.append(f"\t\t- [{met.name}](#{link})")
        func: FunctionDocumentation
        for func in mod.functions:
            link = _escape_link(f"{mod.name.lower()}{func.name.lower()}")
            contents.append(f"\t- [{func.name}](#{link})")
        markdown.extend(mod.to_markdown())
    if table_of_contents:
        while contents:
            markdown.insert(0, contents.pop())
        markdown.insert(0, "**Table of Contents**\n")
    markdown.insert(0, f"{description}\n")
    if title != "":
        markdown.insert(0, f"# {title}\n")
    output: str = "\n".join(markdown)
    if not latex_pagebreak:
        output = output.replace("\\pagebreak", "")
    return output
