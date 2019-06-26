import setuptools
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from os import path

cwd = path.dirname(__file__) + '%s'

ext_modules = [
    Extension("yalabsvc", [cwd % "services/yalabsvc.py"]),
    Extension("yalabdns", [cwd % "services/yalabdns.py"]),
    Extension("ymaster", [cwd % "services/ymaster.py"]),
    Extension("yclient", [cwd % "services/yclient.py"]),
    Extension("yconst", [cwd % "services/yconst.py"]),
    Extension("yglobal", [cwd % "services/yglobal.py"]),
    Extension("ysecret", [cwd % "services/ysecret.py"])
]

setup(
    name = 'yalabsvc',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)

# python compile.py build_ext --inplace
