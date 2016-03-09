# coding: utf-8
# photofs
# Copyright (C) 2012-2014 Moses Palmér
# Copyright (C) 2015-2016 James Bowen
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

import sys

from photofs import *


def main():
    import argparse

    default_root_paths = {"tag-path" :   ("Tags", "Name of directory of images sorted by tags."),
                          "event-path" : ("Events", "Name of directory of images sorted by events."),
                          "date-path" :  ("Date", "Name of directory of images sorted by time taken."),
                          }

    parser = argparse.ArgumentParser(
        prog = 'photofs',
        add_help = True,
        description =
            'Explore tagged images from Shotwell in the file system.',
        epilog =
            'In addition to the command line options specified above, this '
            'program accepts all standard FUSE command line options.')

    parser.add_argument('mountpoint',
        help = 'The file system mount point.')

    parser.add_argument('--debug', '-d',
        help = 'Enable debug logging.',
        type = bool)

    parser.add_argument('--foreground', '-f',
        help = 'Run the daemon in the foreground.',
        action = 'store_true')

    # Add a --*-path and --no-* option for each supported root path
    for path, values in default_root_paths.items():
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--%s" % path, default = values[0], help = values[1])
        group.add_argument("--no-%s" % path.split('-',1)[0], dest = path,
                           action = 'store_const', const = None,
                           help = "Disable %s." % path)

    parser.add_argument('--date-format',
        help = 'The format to use for timestamps.')

    fuse_args = {}
    class OAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string):
            try:
                name, value = values[0].split('=')
            except ValueError:
                name, value = values[0], True
            fuse_args[name] = value
    parser.add_argument('-o',
        help = 'Any FUSE options.',
        nargs = 1,
        action = OAction)

    # Add image source specific command line arguments
    for source in ImageSource.SOURCES.values():
        source.add_arguments(parser)

    # First, let args be the argument dict, but remove undefined values
    args = {name: value
        for name, value in vars(parser.parse_args()).items()
        if not value is None}

    # Then pop these known items and pass them on to the FUSE constructor
    fuse_args.update({name: args.pop(name)
        for name in (
            'foreground',
            'debug')
        if name in args})

    try:
        photo_fs = PhotoFS(**args)
        fuse.FUSE(photo_fs, args['mountpoint'], fsname = 'photofs', **fuse_args)
    except Exception as e:
        import traceback; traceback.print_exc()
        try:
            sys.stderr.write('%s\n' % e.args[0] % e.args[1:])
        except:
            sys.stderr.write('%s\n' % str(e))


main()
