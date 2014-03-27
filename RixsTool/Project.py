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
from RixsTool.ItemContainer import ItemContainer

from RixsTool.IO import IODict
from RixsTool.Items import SpecItem, ScanItem, ImageItem, StackItem

DEBUG = 0


class RixsProject(object):

    __doc__ = """The :py:class:`RixsProject` class is used to read raw data related to a RIXS measurement. Internally
    it organizes the raw data in instances of type :py:class:`Items.DataItem` and real valued functions in
    :py:class:`Items.FunctionItems`. All data items are stored in the project tree, a hierachical data structure.
    The tree itself consists of nodes of type :py:class:`datahandling.ItemContainer`.

    On the top level, the tree divides the data items in containers depeding on the  dimensionality of their data.
    Two dimensional input for example is treated as an image.

    **TODO**:
        * Implement HDF Backend..
    """

    def __init__(self):
        #
        # Input readers
        #
        self.inputReaders = IODict.inputReaderDict()

        #
        # Identifier dict
        #
        self.__idDict = {}

        #
        # Data tree
        #
        self.projectRoot = ItemContainer()
        #self.projectRoot.addChildren(
        #    [ItemContainer(parent=self.projectRoot, label=key)\
        #     for key in ['Spectra', 'Images', 'Stacks']])
        for label in ['Spectra', 'Images', 'Stacks']:
            self.addGroup(label)
        if DEBUG >= 1:
            print('RixsProject.__init__ -- projectRoot.childCount: %d' % self.projectRoot.childCount())
            print('RixsProject.__init__ -- projectRoot.__idDict: %s' % str(self.__idDict))

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

    def __contains__(self, item):
        """
        :param ItemContainer or str item: Method determines if the given container is already in the tree.

        If a string is provided as argument, the function determines if said string is used as a label for a
        container in the tree. If an ItemContainer is provided, the function looks if the item ID is already
        present in the tree.

        :return bool: True or False, depending of item can be found

        :raises ValueError: If the provided item is neither of type string nor an ItemContainer
        """
        if isinstance(item, str):
            llist = self.__idDict.keys()
        elif isinstance(item, ItemContainer):
            item = item.getID()
            llist = self.__idDict.values()
        else:
            raise ValueError('RixsProject.__contains__ -- Argument must be of type string or ItemContainer')
        return item in llist

    def getIdDict(self):
        # TODO: Function for debugging purposes
        return self.__idDict

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

    def addGroup(self, label, node=None):
        """
        :param str label: Unique label for the container
        :param ItemContainer node: Parent for the new container. Defaults to None, the parent in that case is the root.

        Creates a new container object in the parent container node

        :returns: The created :class:`datahandling.ItemContainer`
        :rtype: ItemContainer
        :raises ValueError: if the label is already present in the project
        """
        if DEBUG >= 1:
            print('RixsProject.addItem -- called')
        if label in self.__idDict:
            raise ValueError("RixsProject.addItem -- Item key '%s' already present" % label)
        if not node:
            node = self.projectRoot
        container = ItemContainer(
            item=None,
            parent=node,
            label=label
        )
        node.addChildren([container])
        self.__idDict[container.label] = container.getID()
        return container

    def removeContainer(self, label):
        container = self.__getitem__(label)
        if container.childCount():
            if DEBUG >= 1:
                print('RixsProject.removeContainer -- Has children')
            for child in container.children:
                self.removeContainer(child.label)
        parentContainer = container.parent
        idx = container.childNumber()
        del(parentContainer.children[idx])
        del(self.__idDict[label])

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
        if DEBUG >= 1:
            print("RixsProject.read -- Received '%s' file" % fileType)
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
    directory = '/home/truter/lab/mock_folder/'
    project = RixsProject()
    project.crawl(directory)

    print(project['LBCO0497.edf'])
    print(project['Images'])

if __name__ == '__main__':
    unitTest_RixsProject()