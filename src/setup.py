from distutils.core import setup

from Cython.Build import cythonize

setup(
    ext_modules=cythonize(module_list=[
                          "Models\\Transaction.py", "Models\\BlockDAG\\BlockCommit.py", "Models\\BlockDAG\\BlockDAGraph.py"],
                          # annotate=True
                          ),
)
