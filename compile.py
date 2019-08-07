import setuptools
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from os import path

cwd = path.dirname(__file__) + '%s'

ext_modules = [
    Extension("yalabsvc", [cwd % "source/yalabsvc.py"]),
    Extension("yalabdns", [cwd % "source/yalabdns.py"]),
    Extension("ymaster", [cwd % "source/ymaster.py"]),
    Extension("yclient", [cwd % "source/yclient.py"]),
    Extension("yconst", [cwd % "source/yconst.py"]),
    Extension("yglobal", [cwd % "source/yglobal.py"]),
    Extension("ysecret", [cwd % "source/ysecret.py"])
]

setup(
    name = 'yalabsvc',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)

# python compile.py build_ext --inplace
