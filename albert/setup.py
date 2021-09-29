import codecs
import glob
import hashlib
import os
import re
import shlex
import subprocess
import tarfile
import tempfile
import urllib.request

from packaging import version
from pkg_resources import parse_requirements
from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install


here = os.path.abspath(os.path.dirname(__file__))


def proto_compile(output_path):
    import grpc_tools.protoc

    cli_args = ['grpc_tools.protoc',
                '--proto_path=src/proto', f'--python_out={output_path}',
                f'--grpc_python_out={output_path}'] + glob.glob('src/proto/*.proto')

    code = grpc_tools.protoc.main(cli_args)
    if code:  # hint: if you get this error in jupyter, run in console for richer error message
        raise ValueError(f"{' '.join(cli_args)} finished with exit code {code}")
    # Make pb2 imports in generated scripts relative
    for script in glob.iglob(f'{output_path}/*.py'):
        with open(script, 'r+') as file:
            code = file.read()
            file.seek(0)
            file.write(re.sub(r'\n(import .+_pb2.*)', 'from . \\1', code))
            file.truncate()


class Install(install):
    def run(self):
        proto_compile(os.path.join(self.build_lib, 'src', 'proto'))
        super().run()


class Develop(develop):
    def run(self):
        proto_compile(os.path.join('src', 'proto'))
        super().run()


with open('requirements.txt') as requirements_file:
    install_requires = list(map(str, parse_requirements(requirements_file)))

# loading version from setup.py
with codecs.open(os.path.join(here, 'src/__init__.py'), encoding='utf-8') as init_file:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", init_file.read(), re.M)
    version_string = version_match.group(1)

setup(
    name='src',
    version=version_string,
    cmdclass={'install': Install, 'develop': Develop},
    packages=find_packages(),
    package_data={'src': ['proto/*']},
    include_package_data=True,
    license='MIT',
    setup_requires=['grpcio-tools'],
    install_requires=install_requires,
)
