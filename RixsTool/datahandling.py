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

from os.path import abspath as OsAbsPath  # Better than normalized, absolute version of path
from os.path import splitext as OsPathSplitext
from os.path import join as OsPathJoin
from os import walk as OsWalk
from uuid import uuid4

from RixsTool.IO import IODict
from RixsTool.DataItem import SpecItem, ScanItem, ImageItem, StackItem

DEBUG = 1


class ItemContainer(object):
    __doc__ = """The :class:`ItemContainer` class is the basic building block of a tree like data structure. Within
     the tree hierarchy a container can either be a node or a leave. Nodes have zero or more children, while leaves
     reference an instance of the class :py:class:`DataItem.DataItem`. Both uses of the item container can be
     distinguished using the :func:`hasItem` respectively :py:func:`hasChildren`. Every item container except for
     the top most has a parent pointer and a unique identifier. The identifier can savely be assumed to be random and
     is provided at the moment of instantiation by the :func:`uuid.uuid4`

     .. py:attribute:: __identifier

        Randomly generated identifier for the container

     .. py:attribute:: _item

        Reference to a :py:class:`DataItem.DataItem` instance. None per default

     .. py:attribute:: _data

        List containing the names of attributes of a :py:class:`DataItem.DataItem` that might be of interest for
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
            self.label = item.key
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

        Gives information stored in an :py:class::`DataItem` by calling a corresponding member function that returns
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
        :rtype: None or DataItem
        """
        return self._item

    def setItem(self, item):
        """
        :param DataItem item:
        :returns: Depending on success or failure of the method it returns True or False
        :rtype: None or DataItem
        """
        if len(self.children) and DEBUG >= 1:
            # TODO: Raise exception? Return False?
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


class RixsProject(object):

    __doc__ = """The :py:class:`RixsProject` class is used to read raw data related to a RIXS measurement. Internally
    it organizes the raw data in instances of type :py:class:`DataItem.DataItem`. All data items are stored in the
    project tree, a hierachical data structure. The tree itself consists of instances of type
    :py:class:`datahandling.ItemContainer`.

    On the top level, the tree divides the data items in containers depeding on the
    dimensionality of their data. Two dimensional input for example is treated as an image.

    **TODO:**
        * Add remove functionality here (and not in RixsTool.Models)
    """

    def __init__(self):
        #
        # Input readers
        #
        self.inputReaders = IODict.inputReaderDict()

        #
        # Data tree
        #
        self.projectRoot = ItemContainer()
        self.projectRoot.addChildren(
            [ItemContainer(parent=self.projectRoot, label=key)\
             for key in ['Spectra', 'Images', 'Stacks']])
        print('RixsProject.__init__ -- projectRoot.childCount:', self.projectRoot.childCount())

        #
        # Identifier dict
        #
        self.__idDict = {}

    def __getitem__(self, key):
        result = None
        identifier = self.__idDict[key]
        for container in self._traverseDFS(self.projectRoot):
            if container.getID() == identifier:
                result = container
                break
        if not result:
            raise KeyError()
        return result

    @staticmethod
    def _traverseDFS(root):
        yield root
        for child in root.children:
            for container in RixsProject._traverseDFS(child):
                yield container

    def groupCount(self):
        return self.projectRoot.childCount()

    def image(self, key):
        """
        :param str key: Identifier of the image

        Image -> 2D numpy array. TODO: Try to cast items in form of 2d ndarray?

        :returns: Image from the input reader
        :rtype: ImageItem
        """
        raise NotImplementedError('RixsProject.image -- To be implemented')

    def stack(self, key):
        """
        Stack -> Sequence of images, i.e. 3D numpy array
        """
        raise NotImplementedError('RixsProject.stack -- ..to be implemented')

    def spectrum(self, key):
        """
        Stack -> Sequence of images, i.e. 3D numpy array
        """
        raise NotImplementedError('RixsProject.spectrum -- ..to be implemented')

    def addItem(self, item):
        """
        :param DataItem item: Item to be inserted into the project tree

        Item is wrapped in :class:`datahandling.ItemContainer` and inserted into the tree.
        The insertion node depdends on the type of item.

        **TODO:**
        * Add remove functionality here (c.f. RixsTool.Models)

        :returns: Container of item
        :rtype: ItemContainer
        :raises TypeError: if the item type is unknown
        :raises ValueError: if the item.key() is already present
        """
        if DEBUG >= 1:
            print('RixsProject.addItem -- called')
        if item.key() in self.__idDict:
            raise ValueError("RixsProject.addItem -- Item key '%s' already present" % item.key())
        if isinstance(item, ScanItem) or isinstance(item, SpecItem):
            node = self.projectRoot.children[0]
        elif isinstance(item, ImageItem):
            node = self.projectRoot.children[1]
        elif isinstance(item, StackItem):
            node = self.projectRoot.children[2]
        else:
            raise TypeError("RixsProject.addItem -- unknown item type '%s'" % type(item))
        container = ItemContainer(
            item=item,
            parent=node
        )
        node.addChildren([container])
        self.__idDict[item.key()] = container.getID()
        return container

    def read(self, fileName):
        """
        :param str fileName: File name including path to file

        RixsProject stores a number of different reader for all sorts of file formats. The file stored under
        file name is registered with a matching reader.

        :returns: List of raw data wrapped in :class:`datahandling.ItemContainer`
        :rtype: list
        :raises TypeError: if the item type is unknown
        """
        # Try to guess filetype
        name, ext = OsPathSplitext(fileName)
        fileType = ext.replace('.', '').lower()
        if fileType in self.inputReaders.keys():
            reader = self.inputReaders[fileType]
        else:
            raise TypeError("RixsProject.read -- Unknown file type '%s'" % fileType)
        itemList = reader.itemize(fileName)
        return itemList

    def crawl(self, directory):
        """
        :param str directory: Root directory for the crawler to start

        Reads every file of known file type contained in directory and its subdirectories and adds it
        to the project.
        """
        walk = OsWalk(OsAbsPath(directory))
        if DEBUG >= 1:
            print("RixsProject.crawl -- crawling '%s'" % directory)
        for path, dirs, files in walk:
            if DEBUG >= 1:
                print('RixsProject.crawl -- current path: %s' % path)
            for ffile in files:
                absName = OsPathJoin(path, ffile)
                try:
                    itemList = self.read(absName)
                except TypeError:
                    if DEBUG >= 1:
                        print("RixsProject.crawl -- unkown filetype '%s'" % absName)
                    continue
                for item in itemList:
                    if DEBUG >= 1:
                        print("RixsProject.crawl -- adding Item '%s'" % str(item))
                    self.addItem(item)


def unitTest_RixsProject():
    #directory = r'C:\Users\tonn\lab\mockFolder\Images'
    directory = '/home/truter/lab/mock_folder/Images'
    project = RixsProject()
    project.crawl(directory)

    print(project['LBCO0497.edf'])

    return

if __name__ == '__main__':
    unitTest_RixsProject()