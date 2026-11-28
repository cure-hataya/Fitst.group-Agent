from setuptools import setup, Extension
import pybind11

cpp_args = ['/std:c++17'] 

ext_modules = [
    Extension(
        'cpp_stats',                
        sources=['statistics.cpp'],
        include_dirs=[pybind11.get_include()],
        language='c++',
        extra_compile_args=cpp_args,
    ),
]

setup(
    name='cpp_stats',
    version='1.0',
    description='C++ statistics module for finance app',
    ext_modules=ext_modules,
)