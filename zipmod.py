from __future__ import print_function
import sys

from argparse import ArgumentParser
from configparser import ConfigParser
from os import walk
from os.path import join, relpath
from zipfile import ZipFile
from Sword import SWMgr


OUTPUT_HELP = 'The name of the output directory.'


class ZipModule(object):
    def __init__(self):
        self.args = ArgumentParser()
        self.args.add_argument('-o', '--output', help=OUTPUT_HELP,
                               default=None)
        self.args.add_argument('modules', nargs='+')
        self.sword = SWMgr()

    def validate_module(self, module):
        mod = self.sword.getModule(module)
        return mod

    def get_output_dir(self):
        arg = self.arguments.output
        if arg is None:
            return '.'
        return arg

    def get_zipfile_name(self, path, module):
        return join(path, module + '.zip')

    def write_conf_file(self, archive, module):
        # There is no deterministic way to guarantee module name and conf file
        # are in alignment. So we do it the hard way
        prefix_path = module.getConfigEntry('PrefixPath')
        config_path = join(prefix_path, 'mods.d')
        found_path = None
        for cwd, subdirs, files in walk(config_path):
            for fname in files:
                config = ConfigParser(strict=False, allow_no_value=True)
                config.read(join(cwd, fname))
                if config.sections()[0] == module.getName():
                    found_path = join(cwd, fname)
        if found_path is not None:
            archive.write(found_path, relpath(found_path, prefix_path))
        else:
            print('Unable to locate config file for module', module.getName())
            sys.exit(2)

    def write_data_files(self, archive, module):
        full_data_path = module.getConfigEntry('AbsoluteDataPath')
        # Walk the tree
        for cwd, subdirs, files in walk(full_data_path):
            for filename in files:
                data = join(full_data_path, cwd, filename)
                archivepath = relpath(data, self.sword.prefixPath)
                archive.write(data, archivepath)

    def do_the_things(self):
        self.arguments = self.args.parse_args()
        modules = []
        # Get the module objects
        for module in self.arguments.modules:
            print('Writing zip file for', module)
            swmod = self.validate_module(module)
            if swmod is None:
                print("Error: module {0} not found".format(module))
                sys.exit(1)
            modules.append((module, swmod))
        output_path = self.get_output_dir()
        for module, swmod in modules:
            archive_name = self.get_zipfile_name(output_path, module)
            archive = ZipFile(archive_name, mode='w')
            self.write_conf_file(archive, swmod)
            self.write_data_files(archive, swmod)


if __name__ == '__main__':
    zipmodule = ZipModule()
    zipmodule.do_the_things()
