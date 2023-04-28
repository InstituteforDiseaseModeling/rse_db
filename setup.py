from os import path

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = dict()

for fn in ["", "_dev", "_docs"]:
    with open("requirements{}.txt".format(fn)) as dev_requirement_file:
        requirements[fn.replace("_", "") if fn else "default"] = dev_requirement_file.read().split("\n")

extras_require = dict(full=requirements["default"], dev=requirements["dev"], doc=requirements["docs"])
setup_requirements = ["pytest-runner"]
test_requirements = ["pytest"]

setup(
    name="rse_db",
    version="1.0.3",
    description="RSE-DB provides some common tools for working with dbs",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/markdown",
    url="https://github.com/InstituteforDiseaseModeling/rse_db",
    author="Institute for Disease Modeling - RSE Team",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="rse-core",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    license="MIT License",
    install_requires=requirements["default"],
    setup_requires=setup_requirements,
    extras_requires=extras_require,
    test_suite="tests",
    tests_require=test_requirements,
    project_urls={
        "Bug Reports": "https://github.com/InstituteforDiseaseModeling/rse_db/issues",
        "Source": "https://github.com/InstituteforDiseaseModeling/rse_db",
    },
)
