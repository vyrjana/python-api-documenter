from setuptools import setup, find_packages

setup(
    name="api-documenter",
    version="0.2.0",
    author="Ville Yrjänä",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    url="https://github.com/vyrjana/python-api-documenter",
    project_urls={
        "Bug Tracker": "https://github.com/vyrjana/python-api-documenter/issues",
    },
    license="MIT",
    description="A package for conveniently generating documentation of a Python API through introspection.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
)
