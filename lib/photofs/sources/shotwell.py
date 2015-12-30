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

from xdg.BaseDirectory import xdg_data_dirs

from .. import *

import traceback

# Try to import sqlite
try:
    import sqlite3
except ImportError:
    sqlite = None


# XXX: This needs to get names from args for different root directories or
#      we simply hardcode them ... but they still need to be known
@ImageSource.register('shotwell')
class ShotwellSource(FileBasedImageSource):
    """Loads images and videos from Shotwell.
    """
    def __init__(self, *args, **kwargs):
        if sqlite3 is None:
            raise RuntimeError('This program requires sqlite3')

        for key in ["tag_path", "date_path", "event_path"]:
            val = kwargs.get(key, None)
            setattr(self, key, val)
            if key in kwargs:
                del kwargs[key]

        super(ShotwellSource, self).__init__(*args, **kwargs)

    @property
    def default_location(self):
        """Determines the location of the *Shotwell* database.

        :return: the location of the database, or ``None`` if it cannot be
            located
        :rtype: str or None
        """
        for d in xdg_data_dirs:
            result = os.path.join(d, 'shotwell', 'data', 'photo.db')
            if os.access(result, os.R_OK):
                return result

    def load_tags(self):

        print "Running load_tags()."

        db = sqlite3.connect(self._path)
        try:
            # The descriptions of the different image tables; the value tuple is
            # the header of the ID in the tag table, the map of IDs to images
            # and whether the table contains videos
            db_tables = {
                'phototable': ('thumb', {}, False),
                'videotable': ('video-', {}, True)}

            # Load events
            event_tags = {}

            if self.event_path is not None:
                print " - Loading events."
                results = db.execute("""
                    SELECT id,name FROM EventTable
                    WHERE name != "" and name is not NULL""")
                #results = []
                for r_id, r_name in results:
                    print "     Adding event '{}' (id={})".format(r_name, r_id)
                    event_tags[r_id] = self._make_tags(os.path.join(os.path.sep, self.event_path, r_name))

            # Load the images
            print " - Loading images."
            for table_name, (header, images, is_video) in db_tables.items():
                results = db.execute("""
                    SELECT id, filename, exposure_time, title, event_id
                        FROM %s""" % table_name)
                for r_id, r_filename, r_exposure_time, r_title, r_event in results:
                    images[r_id] = FileBasedImage(
                        r_title,
                        r_filename,
                        r_exposure_time,
                        is_video)
                    if r_event in event_tags:
                        event_tags[r_event].add(images[r_id])
                    if self.date_path:
                        date = time.strftime("%Y/%m/%d", images[r_id].timestamp.timetuple())
                        tag = self._make_tags(os.path.join(os.path.sep, self.date_path, date))
                        tag.add(images[r_id])

            if self.tag_path is not None:
                # Load the tags
                print " - Loading tags."

                results = db.execute("""
                    SELECT name, photo_id_list
                        FROM tagtable
                        ORDER BY name""")
                for r_name, r_photo_id_list in results:
                    # Ignore unused tags
                    if not r_photo_id_list:
                        continue

                    # Hierachial tag names start with '/' but normal tags do not
                    # Ensure path does NOT start with '/'
                    if r_name[0] == '/':
                        path = r_name[1:]
                    else:
                        path = r_name

                    # Make sure that the tag and all its parents exist
                    # XXX: What if we did /Tags/path_name ??
                    tag = self._make_tags(os.path.join(os.path.sep, self.tag_path, path))

                    # The IDs are all in the text of photo_id_list, separated by
                    # commas; there is an extra comma at the end
                    ids = r_photo_id_list.split(',')[:-1]

                    # Iterate over all image IDs and move them to this tag
                    for i in ids:
                        if i[0].isdigit():
                            # If the first character is a digit, this is a legacy
                            # source ID and an ID in the photo table
                            image = db_tables['phototable'][1].get(int(i))
                        else:
                            # Iterate over all database tables and locate the image
                            # instance for the current ID
                            image = None
                            for table_name, (header, images, is_video) \
                                    in db_tables.items():
                                if not i.startswith(header):
                                    continue
                                image = images.get(int(i[len(header):], 16))
                                break

                        # Verify that the tag only references existing images
                        if image is None:
                            continue

                        # Remove the image from the parent tags
                        parent = tag.parent
                        while parent is not None:
                            for k, v in parent.items():
                                if v == image:
                                    del parent[k]
                            parent = parent.parent

                        # Finally add the image to this tag
                        tag.add(image)

        except:
            traceback.print_exc()

        finally:
            print "Done"
            db.close()
