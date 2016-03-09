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

def _names():
    """Lists the names of all resources in this package.

    :return: the names of all resources
    :rtype: [str]
    """
    import os
    import pkg_resources

    return (None
        or pkg_resources.resource_listdir('photofs', 'sources')
        or os.listdir(os.path.dirname(__file__)))

__all__ = [name.rsplit('.', 1)[0]
    for name in _names()
    if name.endswith('.py') and not name[0] == '_']
