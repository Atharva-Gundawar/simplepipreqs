#!/usr/bin/env python
# -*- coding: utf-8 -*-import os

from pathlib import Path
import subprocess
from yarg import json2package
from yarg.exceptions import HTTPError
import requests
import argparse
import os,sys

try:
    from pip._internal.operations import freeze
except ImportError:  # pip < 10.0
    from pip.operations import freeze


def get_installed_packages(pip_version="pip"):
    installed_with_versions = []
    installed = []
    stdout,stderr = subprocess.Popen([pip_version , "freeze"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT).communicate()
    for i in stdout.splitlines():
        installed_with_versions.append(i.decode("utf-8"))
        installed.append(i.decode("utf-8").split('==')[0])
    return installed_with_versions,installed

def get_imports_info(module, pypi_server="https://pypi.python.org/pypi/", proxy=None):
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
        return "# " + str(module) + " version not found"
    return str(module) + '==' + str(data.latest_release_id)

def get_project_imports(directory = os.curdir):
    modules =[]
    for path, subdirs, files in os.walk(directory):
        for name in files:
            if name.endswith('.py'):
                contents = Path(os.path.join(path, name)).read_text().split('\n')
                for lines in contents:
                    words = lines.split(' ')
                    if 'import' == words[0] or 'from' == words[0]:
                        line_module = words[1].split('.')[0].split(',')
                        for module in line_module:
                            if module and module not in modules:
                                modules.append(module)
                                print('found {} in {}'.format(module,name))
            elif name.endswith('.ipynb'):
                contents = json.loads(Path(os.path.join(path, name)).read_text())
                for cell in contents["cells"]:
                    for line in cell["source"]:
                        words = line.split(' ')
                        if 'import' == words[0] or 'from' == words[0]:
                            line_module = words[1].split('.')[0].split(',')
                            for module in line_module:
                                module = module.split('\n')[0]
                                if module and module not in modules:
                                    modules.append(module)
                                    print('found {} in {}'.format(module,name))

    return modules

def init(args):
    output_text = []
    modules = get_project_imports() if args['path'] is None else get_project_imports(args['path'])
    installed_with_versions,installed = get_installed_packages("pip3") if args['version'] is None else get_installed_packages(args['version'])

    for mod in modules:
        if mod in installed:
            print("Searching {} locally".format(mod))
            output_text.append(installed_with_versions[installed.index(mod)])
        else:
            print("{} not found locally, Searching online".format(mod))
            output_text.append(get_imports_info(mod))
    print('Genrating requirements.txt ... ')
    if args['path']:    
        with open( args['path'] + "/requirements.txt", 'w') as f:
            f.write("\n".join(map(str, list(set(output_text)))))
            print("Successfuly created/updated requirements.txt")
    else:
        with open("requirements.txt", 'w') as f:
            f.write("\n".join(map(str, list(set(output_text)))))
            print("Successfuly created/updated requirements.txt")
def main():  
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--version",type=str,help="Pip version")
    ap.add_argument("-p", "--path", type=str,help="Path to target directory")
    args = vars(ap.parse_args())
    try:
        init(args)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()