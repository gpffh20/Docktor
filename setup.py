from setuptools import find_packages, setup


setup(
    name="docktor",
    version="0.1.0",
    description="Docktor CLI",
    py_modules=["main"],
    packages=find_packages(include=["app", "app.*"]),
    install_requires=[
        "annotated-doc==0.0.4",
        "click==8.3.1",
        "markdown-it-py==4.0.0",
        "mdurl==0.1.2",
        "Pygments==2.20.0",
        "rich==14.3.3",
        "shellingham==1.5.4",
        "typer==0.24.1",
    ],
    entry_points={
        "console_scripts": [
            "docktor=main:main",
        ]
    },
)
