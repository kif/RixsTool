#/*##########################################################################
# Copyright (C) 2014 European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# This toolkit is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# PyMca is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# PyMca; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# PyMca follows the dual licensing model of Riverbank's PyQt and cannot be
# used as a free plugin for a non-free program.
#
# Please contact the ESRF industrial unit (industry@esrf.fr) if this license
# is a problem for you.
#############################################################################*/
__author__ = "Tonn Rueter - ESRF Data Analysis Unit"

from uuid import uuid4

DEBUG = 0


class ItemContainer(object):
    __doc__ = """The :class:`ItemContainer` class is the basic building block of a tree like data structure. Within
     the tree hierarchy a container can either be a node or a leave. Nodes have zero or more children, while leaves
     reference an instance of the class :py:class:`Items.ProjectItem`. Both uses of the item container can be
     distinguished using the :func:`hasItem` respectively :py:func:`hasChildren`. Every item container except for
     the top most has a parent pointer and a unique identifier. The identifier can savely be assumed to be random and
     is provided at the moment of instantiation by the :func:`uuid.uuid4`

     .. py:attribute:: __identifier

        Randomly generated identifier for the container

     .. py:attribute:: _item

        Reference to a :py:class:`Items.ProjectItem` instance. None per default

     .. py:attribute:: _data

        List containing the names of attributes of a :py:class:`Items.ProjectItem` that might be of interest for
        a display (c.f. :py:class:`Models.ProjectView`)

     .. py:attribute:: parent

        :class:`ItemContainer` instance that is higher in the tree hierarchie than the current instance

     .. py:attribute:: children

        List of :class:`ItemContainer` instance that are lower in the tree hierarchie than the current instance

     .. py:attribute:: label

        String naming the container."""

    def __init__(self, item=None, parent=None, label=None):
        #self._data = data if data is not None else [] # Dict or OrderedDict here?
        self.__identifier = uuid4()
        self._item = item
        self._data = ['key', 'description', 'shape', 'dtype']
        self.parent = parent
        self.children = []
        if label:
            self.label = label
        elif item:
            #self.label = item.key
            self.label = item.key()
        else:
            self.label = ''

    #
    # Compare two containers
    #
    def getID(self):
        return self.__identifier

    def __eq__(self, other):
        return self.getID() == other.getID()

    #
    # Methods acting on ItemContainer.children or ItemContainer.parent
    #
    def hasChildren(self):
        return len(self.children) > 0

    def childCount(self):
        return len(self.children)

    def childNumber(self):
        """
        :returns: Index in parents children list. If parent is None, -1 is returned
        :rtype: int
        """
        if self.parent:
            siblings = self.parent.children
            idx = siblings.index(self)
        else:
            idx = -1
        return idx

    #
    # Methods acting on ItemContainer._data
    #

    def columnCount(self):
        """
        :returns: Number of columns to be displayed in a QTreeView
        :rtype: int
        """
        return len(self._data)

    def setData(self, pos, attr):
        """
        :param int pos: Determines at which position the new column is inserted
        :param str attr: Determines which attribute is displayed in the new column
        :returns: Depending on success or failure of the method it returns True or False
        :rtype: bool
        """
        # Is this method even needed?
        if (pos < 0) or (pos >= len(self._data)):
            return False
        if not hasattr(self._data, attr):
            return False
        head = self._data[0:pos]
        tail = self._data[pos:]
        self._data = head + [attr] + tail
        return True

    def data(self, idx):
        """
        :param int idx: Determines which attribute of the item is called

        Gives information stored in an :py:class::`ProjectItem` by calling a corresponding member function that returns
        a string representation of said attribute.

        :returns: Depending on success or failure of the method it returns True or False
        :rtype: bool
        """
        if (idx < 0) or idx >= len(self._data):
            raise IndexError('ItemContainer.data -- Index out of range')
        attr = self._data[idx]
        val = getattr(self._item, attr)
        if callable(val):
            val = val()
        return val

    #
    # Methods acting on ItemContainer._item
    #

    def hasItem(self):
        """
        :returns: Checks if the container item is not None
        :rtype: bool
        """
        return self._item is not None

    def item(self):
        """
        :returns: Returns the data stored in the container
        :rtype: None or ProjectItem
        """
        return self._item

    def setItem(self, item):
        """
        :param ProjectItem item:
        :returns: Depending on success or failure of the method it returns True or False
        :rtype: None or ProjectItem
        """
        if len(self.children) and DEBUG >= 1:
            # TODO: Raise exception? Return False?
            if DEBUG >= 1:
                print('ItemContainer.setItem -- Instance has children!')
        self._item = item
        return True

    #
    # Methods acting on ItemContainer.children
    #

    def addChildren(self, containerList, pos=-1):
        """
        :param list containerList: List of ItemContainers to be added as child
        :param int pos: Determines where the new children are in ItemContainer.children list. Default: -1, i.e. at the end.
        :returns: Depending on success or failure of the method it returns True or False
        :rtype: bool
        """
        # Modifies self.children
        # Insert ItemContainer instances
        if (pos < -1) or (pos > len(self.children)):
            return False
        if False in [isinstance(child, ItemContainer) for child in containerList]:
            return False
        if pos == -1:
            pos = len(self.children)

        head = self.children[0:pos]
        tail = self.children[pos:]
        self.children = head + containerList + tail
        return True

    def removeChildren(self, pos, count=1):
        """
        :param int pos: Children from this position on are deleted
        :param int count: Determines how many children are deleted. Default: 1
        :returns: Depending on success or failure of the method it returns True or False
        :rtype: bool
        """
        if (pos < 0) or (pos >= len(self.children)):
            return False

        del(self.children[pos:pos+count])
        return True


if __name__ == '__main__':
    pass