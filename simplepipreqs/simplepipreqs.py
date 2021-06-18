#!/usr/bin/env python
# -*- coding: utf-8 -*-import os

from pathlib import Path
import subprocess
from yarg import json2package
from yarg.exceptions import HTTPError
import requests
import argparse
import os
import sys
import json
import threading
import itertools
import time

try:
    from pip._internal.operations import freeze
except ImportError:  # pip < 10.0
    from pip.operations import freeze


def get_installed_packages(pip_version: str = "pip"):
    installed_with_versions = []
    installed = []
    stdout, stderr = subprocess.Popen(
        [pip_version, "freeze"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
    for i in stdout.splitlines():
        installed_with_versions.append(i.decode("utf-8"))
        installed.append(i.decode("utf-8").split('==')[0])
    return installed_with_versions, installed


def get_version_info(module: str, pypi_server: str = "https://pypi.python.org/pypi/", proxy=None):
    try:
        response = requests.get(
            "{0}{1}/json".format(pypi_server, module), proxies=proxy)
        if response.status_code == 200:
            if hasattr(response.content, 'decode'):
                data = json2package(response.content.decode())
            else:
                data = json2package(response.content)
        elif response.status_code >= 300:
            raise HTTPError(status_code=response.status_code,
                            reason=response.reason)
    except HTTPError:
        return None
    return str(module) + '==' + str(data.latest_release_id)


def get_project_imports(directory: str = os.curdir):
    modules = []
    for path, subdirs, files in os.walk(directory):
        for name in files:
            if name.endswith('.py'):
                # print(path)
                with open(os.path.join(path, name)) as f:
                    contents = f.readlines()
                for lines in contents:
                    words = lines.split(' ')
                    if 'import' == words[0] or 'from' == words[0]:
                        line_module = words[1].split('.')[0].split(',')
                        for module in line_module:
                            module = module.split('\n')[0]
                            if module and module not in modules:
                                modules.append(module)
                                # print('found {} in {}'.format(module,name))
            elif name.endswith('.ipynb'):
                with open(str(Path(os.path.join(path, name)).absolute())) as f:
                    contents = f.readlines()
                listToStr = ' '.join([str(elem) for elem in contents])
                contents = json.loads(listToStr)
                # contents = json.loads(Path(os.path.join(path, name)).absolute().read_text())
                for cell in contents["cells"]:
                    for line in cell["source"]:
                        words = line.split(' ')
                        if 'import' == words[0] or 'from' == words[0]:
                            line_module = words[1].split('.')[0].split(',')
                            for module in line_module:
                                module = module.split('\n')[0]
                                if module and module not in modules:
                                    modules.append(module)
                                    # print('found {} in {}'.format(module, name))

    return modules


def init(args):

    done_imports = False

    def animate_imports():
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if done_imports:

                break
            print('Getting imports ' + c, end="\r")
            sys.stdout.flush()
            time.sleep(0.1)

    t_imports = threading.Thread(target=animate_imports)
    print()
    t_imports.start()

    output_text = []
    modules = get_project_imports(
    ) if args['path'] is None else get_project_imports(args['path'])
    installed_with_versions, installed = get_installed_packages(
        "pip3") if args['version'] is None else get_installed_packages(args['version'])

    done_imports = True
    time.sleep(0.2)
    done_versions = False

    def animate_versions():
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if done_versions:
                print("\033[A                             \033[A")
                break
            print('Getting versions ' + c, end="\r")
            sys.stdout.flush()
            time.sleep(0.1)

    t_versions = threading.Thread(target=animate_versions)
    t_versions.start()

    for mod in modules:
        if mod in installed:
            mod_info = get_version_info(mod)
            if mod_info:
                output_text.append(mod_info)

    done_versions = True
    time.sleep(0.2)

    print('\nGenrating requirements.txt ... ')

    if args['path']:
        with open(args['path'] + "/requirements.txt", 'w') as f:
            f.write("\n".join(map(str, list(set(output_text)))))
            print("Successfuly created/updated requirements.txt")
    else:
        with open("requirements.txt", 'w') as f:
            f.write("\n".join(map(str, list(set(output_text)))))
            print("Successfuly created/updated requirements.txt")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--version", type=str, help="Pip version")
    ap.add_argument("-p", "--path", type=str, help="Path to target directory")
    args = vars(ap.parse_args())
    try:
        init(args)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
