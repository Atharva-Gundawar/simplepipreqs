import os
from pathlib import Path
import subprocess
from yarg import json2package
from yarg.exceptions import HTTPError
import requests
try:
    from pip._internal.operations import freeze
except ImportError:  # pip < 10.0
    from pip.operations import freeze

modules = []
installed_with_versions = []
installed = []
req_text = []

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
    modules = []
    for path, subdirs, files in os.walk(directory):
        for name in files:
            if name.endswith('.py'):
                contents = Path(os.path.join(path, name)).read_text().split('\n')
                for lines in contents:
                    words = lines.split(' ')
                    if 'import' == words[0] or 'from' == words[0]:
                        line_module = words[1].split('.')[0].split(',')
                        for module in line_module:
                            if module not in modules and module:
                                modules.append(module)
                                print('found {} in {}'.format(module,name))
    return modules


modules = get_project_imports()
installed_with_versions,installed = get_installed_packages("pip3")

for mod in modules:
    if mod in installed:
        print("Searching {} locally".format(mod))
        req_text.append(installed_with_versions[installed.index(mod)])
    else:
        print("{} not found locally, Searching online".format(mod))
        req_text.append(get_imports_info(mod))

with open("requirement.txt", 'w') as f:
    f.write("\n".join(map(str, list(set(req_text)))))

