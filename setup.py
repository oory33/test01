from setuptools import setup, Extension

from Cython.Build import cythonize
import Cython.Compiler.Options
Cython.Compiler.Options.docstrings = False

ext_modules = cythonize(
    [
        #akeroyd
        Extension("libs.akeroyd", ["libs/akeroyd.py"]),

        #modulation
        Extension("libs.modulation", ["libs/modulation.py"]),



    ], compiler_directives=dict(
            language_level="3",
            always_allow_keywords=True
        )
)

setup(
    name="test01",
    version='1.0.0',
    ext_modules=ext_modules,
    author="ryo",
    author_email="s2222402@ms.geidai.ac.jp",
)
