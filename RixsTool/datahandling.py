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

import RixsTool.io as IO
from os.path import normpath as OsPathNormpath
from os.path import splitext as OsPathSplitext
from os import walk as OsWalk

DEBUG = 1

class ItemContainer(object):
    def __init__(self, item=None, parent=None, label=None):
        #self._data = data if data is not None else [] # Dict or OrderedDict here?
        self._item = item
        self._data = ['key','description', 'shape', 'dtype']
        self.parent = parent
        self.children = []
        if label:
            self.label = label
        elif item:
            self.label = item.key
        else:
            self.label = ''

    #
    # Methods acting on ItemContainer.children or ItemContainer.parent
    #

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
        :param pos: Determines at which position the new column is inserted
        :type pos: int
        :param attr: Determines which attribute is displayed in the new column
        :type pos: str
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
        :returns: Checks if the container has an item
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
        :returns:
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
        :param containerList: List of ItemContainers to be added as child
        :type containerList: list
        :param pos: Determines where the new children are in ItemContainer.children list. Default: -1, i.e. at the end.
        :type pos: int
        :returns: Depending on success or failure of the method it returns True or False
        :rtype: bool
        """
        # Modifies self.children
        # Insert ItemContainer instances
        if (pos < -1) or (pos > len(self.children)):
            return False
        if False in [isinstance(child, ItemContainer) for child in containerList]:
            return False

        head = self.children[0:pos]
        tail = self.children[pos:]
        self.children = head + containerList + tail
        return True

    def removeChildren(self, pos, count=1):
        """
        :param pos: Children from this position on are deleted
        :type pos: int
        :param count: Determines how many children are deleted. Default: 1
        :type count: int
        :returns: Depending on success or failure of the method it returns True or False
        :rtype: bool
        """
        if (pos < 0) or (pos >= len(self.children)):
            return False

        del(self.children[pos:pos+count])
        return True


class RixsProject(object):

    __OPERATION = 'operation'

    DATA_TYPE = 'data' # -> 1d, 2d or 3d numpy array
    EDF_TYPE = 'edf'   # -> Wrapper for edf files
    RAW_TYPE = 'raw'   # -> Wrapper for plaintext data

    # TODO: Use these type too
    RAW_TYPE = 'spec' # -> Wrapper for spec files
    SPEC_TYPE = 'stack' # -> Wrapper for spec files

    typeList = [SPEC_TYPE, EDF_TYPE, RAW_TYPE]

    def __init__(self):
        super(RixsProject, self).__init__()

        #
        # Spec readers
        #
        # TODO: Have readers for specfiles..
        self.specReaders = {
            self.SPEC_TYPE : None
        }

        #
        # Image readers
        #
        self.imageReaders = {
            self.EDF_TYPE : IO.EdfInputReader(),
            self.RAW_TYPE : IO.RawTextInputReader()
        }

        #
        # Data tree
        #
        self.projectRoot = ItemContainer()
        self.projectRoot.addChildren(
            [ItemContainer(parent=self.projectRoot, label=key)\
             for key in ['Spectra','Images','Stacks']])
        print('projectRoot.childCount:',self.projectRoot.childCount())

    def groupCount(self):
        return self.projectRoot.childCount()

    def image(self, key, imageType):
        """
        :param key: Identifier of the image
        :type key: str
        :param imageType: Describtor of image type (edf, raw, ...)
        :type imageType: str

        Image -> 2D numpy array

        :returns: Image from the input reader
        :rtype: ImageItem
        """
        reader = self.imageReaders.get(imageType, None)
        if reader is None:
            raise ValueError("RixsProject.image -- Unknown image type '%s'"%imageType)
        # User reader interface
        keys = reader.keys()
        if key not in keys:
            raise KeyError("RixsProject.image -- Key '%s' not found"%key)
        idx = keys.index(key)
        return reader[idx]

    def addImage(self, image, node=None):
        if not node:
            node = self.projectRoot.children[1] # TODO: Find better way to access children
        child = ItemContainer(
            item=image,
            parent=node
        )
        node.addChildren([child])

    def readImage(self, filename, imageType):
        try:
            reader = self.imageReaders.get(imageType, None)
        except KeyError:
            raise ValueError("RixsProject.readImages -- Unknown image Type '%s'"%imageType)
        keys = reader['FileLocations']
        reader.refresh([filename])
        if filename not in keys:
            keys = reader['FileLocations']
            print(keys)
            idx = keys.index(filename)
            self.addImage(reader[idx])
        return True

    def stack(self, key, index):
        """
        Stack -> Sequence of images, i.e. 3D numpy array
        """
        raise NotImplementedError('RixsProject.stack -- ..to be implemented')

    def spectrum(self, key, index):
        """
        Stack -> Sequence of images, i.e. 3D numpy array
        """
        raise NotImplementedError('RixsProject.spectrum -- ..to be implemented')

    def addFileInfoList(self, fileInfoList):
        if DEBUG == 1:
            print('RixsProject.addFileInfoList -- received fileInfoList (len: %d)'%\
                  len(fileInfoList))
        for info in fileInfoList:
            name = OsPathNormpath(info.completeSuffix())
            suffix = str(info.completeSuffix())
            if suffix.lower not in self.imageReaders.keys():
                raise ValueError("Unknown filetype: '%s'"%suffix)
            reader = self.imageReaders[suffix]
            reader.append(name)
            print(reader)

    def keys(self):
        llist = [reader.getFileList() for reader in self.imageReaders.values()]
        return sum(llist, [])

def unitTest_RixsProject():
    directory = r'C:\Users\tonn\lab\mockFolder'
    project = RixsProject()
    for result in OsWalk(directory):
        currentPath = result[0]
        dirs = result[1]
        files = result[2]
        for file in files:
            root, ext = OsPathSplitext(file)
            filename = currentPath + '\\' + file
            if ext.replace('.','') == project.EDF_TYPE:
                print('Found edf-File:')
                project.readImage(filename, project.EDF_TYPE)
                print(type(project.image(file, project.EDF_TYPE)))

if __name__ == '__main__':
    #unitTest_QDirListModel()
    #rixsImageDir = 'C:\\Users\\tonn\\lab\\rixs\\Images'
    #proj = RixsProject()
    #edfImageList = [OsPathJoin(rixsImageDir,fn) for fn in OsListDir(rixsImageDir)\
    #             if OsPathIsFile(OsPathJoin(rixsImageDir,fn))][1:]
    #proj.readImages(edfImageList, 'edf')
    unitTest_RixsProject()