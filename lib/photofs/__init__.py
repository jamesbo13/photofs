#!/usr/bin/env python
# coding: utf-8
# photofs
# Copyright (C) 2012-2014 Moses Palmér
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

import os
import threading
import time

# For FUSE
import errno
import fuse

from ._image import Image, FileBasedImage
from ._source import ImageSource, FileBasedImageSource
from ._tag import Tag


# Import the actual image sources
from .sources import *


class PhotoFS(fuse.LoggingMixIn, fuse.Operations):
    """An implementation of a *FUSE* file system.

    It presents the tagged image libraries from image sources as a tag tree in
    the file system.

    :param ImageSource source: The image source.

    :param database: An override for the default database file for the
        selected image source.
    :type database: str or None

    :param str tag_path: The directory in the mounted root to contain tags.

    :param str date_path: The directory in the mounted root to contain dates.

    :param str event_path: The directory in the mounted root to contain events

    :param str date_format: The date format string used to construct file names
        from time stamps.

    :raises RuntimeError: if an error occurs
    """

    _ROOT_DIR_DEFAULTS = {"tag_path" :   'Tags',
                          "date_path" :  'Date',
                          "event_path" : 'Event'}

    def __init__(self,
            mountpoint,
            source = list(ImageSource.SOURCES.keys())[0],
            date_format = '%Y-%m-%d_%H-%M-%S',
            **kwargs):
        super(PhotoFS, self).__init__()

        self.source = source
        Image.DATE_FORMAT = date_format

        self.creation = None
        self.dirstat = None
        self.image_source = None
        self.root_dirs = []

        self.handles = {}

        # Create the image source
        self.image_source = ImageSource.get(self.source)(**kwargs)

        try:
            # Make sure the root paths are strings or None
            for key,default in self._ROOT_DIR_DEFAULTS.items():
                val = kwargs.get(key, default)
                if val is not None:
                    val = str(val)
                    setattr(self, key, val)
                    self.root_dirs.append(val)
                else:
                    setattr(self, key, val)

            # Store the current time as timestamp for directories
            self.creation = int(time.time())

            # Use the lstat result of the mount point for all directories
            self.dirstat = os.lstat(mountpoint)

        except Exception as e:
            try:
                raise RuntimeError('Failed to initialise file system: %s',
                    e.args[0] % e.args[1:])
            except:
                raise RuntimeError('Failed to initialise file system: %s',
                    str(e))

    def __getitem__(self, path):
        """Reads the item at ``path``.

        The root component of the path is discarded.

        :param str path: The path for which to find the item.

        :returns: the tag or image
        :rtype: Tag or Image
        """
        print "__get__item(): path='%s'" % (path)

        return self.image_source.locate(path)

    def destroy(self, path):
        pass

    def _getattr(self, path):
        """Performs a stat on ``/root/path``.

        :param str root: The first segment of the path, which contains the
            string that caused this resolver to be picked by
            :class:`PhotoFS`.

        :param str path: The path to resolve. This has to begin with
            :attr:`os.path.sep`.

        :return: a :class:`os.stat_result` object for the path
        :rtype: os.stat_result

        :raises fuse.FuseOSError: if an error occurs
        """
        try:
            item = self.image_source.locate(path)

            if isinstance(item, Image):
                # This is a file
                return item.stat

            elif isinstance(item, dict):
                # This is a directory; this matches both Tag and ImageSource
                return self.dirstat

            else:
                raise RuntimeError('Unknown object: %s', path)

        except KeyError:
            raise fuse.FuseOSError(errno.ENOENT)

    def _readdir(self, path):
        """Performs a directory listing on ``/root/path``.

        :param str root: The first segment of the path, which contains the
            string that caused this resolver to be picked by
            :class:`PhotoFS`.

        :param str path: The path to resolve. This has to begin with
            :attr:`os.path.sep`, and it must be resolved to a dictionary.

        :return: a sequence of strings describing the directory
        :rtype: [str]

        :raises fuse.FuseOSError: if an error occurs
        """
        try:
            item = self.image_source.locate(path)

            if isinstance(item, dict):
                # This is a directory; this matches both Tag and ImageSource
                #return [k
                #    for k, v in item.items()
                #    if self._include_filter(v)]
                return item.keys()
            else:
                raise RuntimeError('Unknown object: %s', path)

        except KeyError:
            raise fuse.FuseOSError(errno.ENOENT)



    def split_path(self, path):
        """Returns the tuple ``(root, rest)`` for a path, where ``root`` is the
        directory immediately beneath the root and ``rest`` is anything after
        that.

        :param str path: The path to split. This must begin with
            :attr:`os.path.sep`.

        :return: a tuple containing the split path, which may be empty strings

        :raises ValueError: if ``path`` does not begin with :attr:`os.path.sep`
        """
        if path[0] != os.path.sep:
            raise ValueError('%s is not a valid path',
                path)
        path = path[len(os.path.sep):]

        if os.path.sep in path:
            return path.split(os.path.sep, 1)
        else:
            return (path, '')

    def getattr(self, path, fh = None):
        try:
            root, rest = self.split_path(path)

            if not rest:
                # Unless path is the root, it must be in the resolvers; the root
                # and any items directly below it are directories

                # XXX: change self.resolvers to self.root_dirs
                if root and not root in self.root_dirs:
                    raise fuse.FuseOSError(errno.ENOENT)
                else:
                    st = self.dirstat
            else:
                # XXX: Don't have separate resolvers, just lookup bits here
                #      based on full path (ie. don't split root and rest)
                st = self._getattr(path)

            return dict(
                # Remove write permission bits
                st_mode = st.st_mode & ~146,

                st_gid = st.st_gid,
                st_uid = st.st_uid,

                st_nlink = st.st_nlink,

                st_atime = st.st_atime,
                st_ctime = st.st_ctime,
                st_mtime = st.st_mtime,

                st_size = st.st_size)

        except KeyError:
            raise fuse.FuseOSError(errno.ENOENT)

        except OSError as e:
            raise fuse.FuseOSError(e.errno)


    def readdir(self, path, offset):
        try:
            root, rest = self.split_path(path)

            if not root:
                items = [d for d in self.root_dirs]
            else:
                items = self._readdir(path)

            # We return tuples instead of strings since fusepy on Python 2.x
            # incorrectly treats unicode as non-string
            return [(i, None, 0)
                for i in items]

        except KeyError:
            raise fuse.FuseOSError(errno.ENOENT)

        except OSError as e:
            raise fuse.FuseOSError(e.errno)

    def open(self, path, flags):
        print "open(): path='%s', flags='%s'" % (path, flags)

        item = self[path]
        if isinstance(item, Image):
            handle = item.open(flags)
            self.handles[id(handle)] = (handle, threading.Lock())
            return id(handle)
        else:
            raise fuse.FuseOSError(errno.EINVAL)

    def release(self, path, fh):
        try:
            handle, lock = self.handles[fh]
            with lock:
                handle.close()
            del self.handles[fh]
        except:
            raise fuse.FuseOSError(errno.EINVAL)

    def read(self, path, size, offset, fh):
        handle, lock = self.handles[fh]
        with lock:
            if handle.tell() != offset:
                handle.seek(offset)
            return handle.read(size)
