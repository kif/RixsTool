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

import sys

if sys.version > '2.4':
    from collections import OrderedDict
else:
    from RixsTool.OrderedDict import OrderedDict
from PyMca.PyMcaIO.EdfFile import EdfFile
from os.path import split as OsPathSplit
from os import access as OsAccess
from os import R_OK as OS_R_OK
import numpy as np
import time
from RixsTool.DataItem import ImageItem

class InputReader(object):
    def __init__(self):
        self.__readerDict = OrderedDict()
        self.itemDict = OrderedDict()
        self._srcType = None
        self.__active = False

    def __len__(self):
        return len(self.keys())

    def __repr__(self):
        inputType = str(self._srcType)
        return '\n\t'.join(['%s %s %s' % (inputType, 'instance at', id(self))] +
                           ['%s -> shape %s' % (item.key, str(item.shape())) for item in self.items() if item])

    def keys(self):
        return self.itemDict.keys()

    def items(self):
        return self.itemDict.values()

    def files(self):
        return self.__readerDict.keys()

    def readers(self):
        return self.__readerDict.values()

    def __initReaders(self, llist):
        """
        :param llist: List of full filename including path
        :type llist: list


        """
        if isinstance(self._srcType, type(None)):
            raise NotImplementedError('InputReader.__initReaders -- Do not instantiate base class')
        for filename in llist:
            print('InputReader.__initReaders -- reading:', filename)
            if not OsAccess(filename, OS_R_OK):
                print("Invalid file '%s'" % filename)
                continue
            path, key = OsPathSplit(filename)
            if len(key) == 0:
                print('InputReader.__initReaders -- len(key) == 0, This should not happen!')
                continue
            if filename not in self.__readerDict.keys():
                self.__readerDict[filename] = self._srcType(filename)
                self.itemDict[key] = None
        return True

    def _setData(self, llist):
        """
        Fills the self.__data dictionary with the corresponding values. This
        funtion needs to be reimplemented in every subclass.
        """
        raise NotImplementedError('InputReader._setData -- Do not instantiate base class')

    def append(self, llist):
        """
        :param llist: List of files to append
        :type llist: list

        Appends new files to self.__filelist if they
        are not already present.
        """
        print('InputReader.append -- llist:',str(llist))
        self.refreshing = True
        self.__initReaders(llist)
        self._setData()
        self.refreshing = False


    def refresh(self):
        '''
        :param llist: List of file names or keys to be refreshed
        :type llist: list

        Resets the entries given in llist if stored in the internal dictionaries
        '''
        # TODO: Implement me..
        raise NotImplementedError("InputReader.refresh -- Here is work to be done..")

class EdfReader(InputReader):
    def __init__(self):
        super(EdfReader, self).__init__()
        self._srcType = EdfFile

    def _setData(self):
        # def __init__(self, key, header, array, fileLocation):
        timeStart = time.time()

        #
        # Consistency check
        #
        if len(self.items()) != len(self.readers()):
            raise IndexError('EdfReader._setData -- Inequal amount of readers and items')


        #
        # Create either ImageItem or StackItem, if single or multiple images are present
        #
        updateDict = OrderedDict()
        for key, item, reader in zip(self.keys(), self.items(), self.readers()):
            if item:
                continue

            numImages = reader.GetNumImages()

            if numImages == 1:
                arr = reader.GetData(0)
                newItem = ImageItem(
                    key=key,
                    header=reader.GetHeader(0),
                    array=np.ascontiguousarray(arr, arr.dtype),
                    fileLocation=reader.FileName
                )
            else:
                print('EDFInputReader._data -- Unsupported number of images in single EDF file')
                newItem = ImageItem(
                    key=key,
                    header='',
                    array=np.zeros((10, 10), dtype=np.uint16),
                    fileLocation=reader.FileName
                )

            updateDict[key] = newItem
        self.itemDict.update(updateDict)

        timeEnd = time.time()
        print('EdfInputReader._setData -- Method finished in %.3f s'%\
              (timeEnd - timeStart))

def unitTest_InputReader():
    rixsImageDir = '/Users/tonn/DATA/rixs_data/Images'
    from os import listdir as OsListDir
    from os.path import isfile as OsPathIsFile, join as OsPathJoin
    edfImageList = [OsPathJoin(rixsImageDir, fn) for fn in OsListDir(rixsImageDir)\
                    if OsPathIsFile(OsPathJoin(rixsImageDir, fn))][1:]

    edfReader = EdfReader()
    #edfReader = InputReader()
    edfReader.append(edfImageList)
    for elem in zip(edfReader.files(), edfReader.keys()):
        print(elem)
    print edfReader

if __name__ == '__main__':
    unitTest_InputReader()