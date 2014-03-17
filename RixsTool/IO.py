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

from PyMca.PyMcaIO.EdfFile import EdfFile
from PyMca.PyMcaIO import specfilewrapper as Specfile
from os.path import split as OsPathSplit
from os import access as OsAccess
from os import R_OK as OS_R_OK
import numpy as np
import time
from RixsTool.DataItem import ImageItem

DEBUG = 1


class IODict(object):
    EDF_TYPE = 'edf'    # -> Wrapper for edf files
    RAW_TYPE = 'raw'    # -> Wrapper for plaintext data

    # TODO: Use these type too
    SPEC_TYPE = 'stack'  # -> Wrapper for spec files

    @staticmethod
    def inputReaderDict():
        ddict = {
            IODict.EDF_TYPE: EdfReader()
        }
        return ddict


class InputReader(object):
    def __init__(self):
        self._srcType = None
        self.key = ''
        self.reader = None

    def __len__(self):
        return len(self.keys())

    def __repr__(self):
        inputType = str(self._srcType)
        return '%s %s %s' % (inputType, 'instance at', id(self))

    def __initReader(self, fileName):
        """
        :param fileName: absolute file name
        :type fileName: str

        Creates reader instance and sets the key.
        """
        if isinstance(self._srcType, type(None)):
            raise NotImplementedError('InputReader.__initReaders -- Do not instantiate base class')
        if DEBUG >= 1:
            print("InputReader.__initReaders -- reading: '%s'" % fileName)
        if not OsAccess(fileName, OS_R_OK):
            return False
        path, name = OsPathSplit(fileName)
        self.key = name
        self.reader = self._srcType(fileName)
        return True

    def itemize(self, fileName):
        """
        :param fileName: File name including absolute path to the file
        :type fileName: str

        Method serves as interface between the different reader types and the DataItem container class.
        :func:`InputReader.itemize` must be reimplemented in every child class.

        :raises ValueError: In case the file is inaccessible
        :raises NotImplementedError: In case the base class is instantiated
        """
        try:
            success = self.__initReader(fileName)
        except NotImplementedError:
            # Reraise error from correct function
            raise NotImplementedError('InputReader.itemize -- Do not instantiate base class')
        if not success:
            raise ValueError("InputReader.itemize -- Invalid file '%s'" % fileName)


class EdfReader(InputReader):
    def __init__(self):
        super(EdfReader, self).__init__()
        self._srcType = EdfFile

    def itemize(self, fileName):
        timeStart = time.time()
        InputReader.itemize(self, fileName)

        numImages = self.reader.GetNumImages()
        llist = []
        if numImages > 1:
            raise NotImplementedError('EdfReader.itemize -- No support for edfs containing multiple images')
            #for idx in range(numImages):
            #    arr = reader.GetData(idx)
            #    newItem = ImageItem(
            #        key=key,
            #        header=reader.GetHeader(0),
            #        array=np.ascontiguousarray(arr, arr.dtype),
            #        fileLocation=reader.FileName
            #    )
        else:
            arr = self.reader.GetData(0)
            newItem = ImageItem(
                key=self.key,
                header=self.reader.GetHeader(0),
                array=np.ascontiguousarray(arr, arr.dtype),
                fileLocation=self.reader.FileName)
            llist += [newItem]

        timeEnd = time.time()
        print('EdfInputReader.itemize -- Method finished in %.3f s' % (timeEnd - timeStart))
        return llist


class SpecFileReader(InputReader):
    def __init__(self):
        super(SpecFileReader, self).__init__()
        self._srcType = Specfile

    def itemize(self, fileName):
        raise NotImplementedError('Shit ain\'t ready yet..')
        timeStart = time.time()
        InputReader.itemize(self, fileName)

        numScans = self.reader.scanno()
        llist = []
        if numScans > 1:
            raise NotImplementedError('EdfReader.itemize -- No support for edfs containing multiple images')
            #for idx in range(numImages):
            #    arr = reader.GetData(idx)
            #    newItem = ImageItem(
            #        key=key,
            #        header=reader.GetHeader(0),
            #        array=np.ascontiguousarray(arr, arr.dtype),
            #        fileLocation=reader.FileName
            #    )
        else:
            scan = self.reader[0]
            newItem = ImageItem(
                key=self.key,
                header=self.reader.GetHeader(0),
                array=np.ascontiguousarray(arr, arr.dtype),
                fileLocation=self.reader.FileName)
            llist += [newItem]

        timeEnd = time.time()
        print('EdfInputReader.itemize -- Method finished in %.3f s' % (timeEnd - timeStart))
        return llist


def unitTest_InputReader():
    #rixsImageDir = '/Users/tonn/DATA/rixs_data/Images'
    rixsImageDir = '/home/truter/lab/rixs/rixs_data/Images'
    from os import listdir as OsListDir
    from os.path import isfile as OsPathIsFile, join as OsPathJoin
    edfImageList = [OsPathJoin(rixsImageDir, fn) for fn in OsListDir(rixsImageDir)\
                    if OsPathIsFile(OsPathJoin(rixsImageDir, fn))][1:]

    edfReader = EdfReader()
    for elem in sum([edfReader.itemize(fn) for fn in edfImageList], []):
        print elem.key
    print(edfReader)

if __name__ == '__main__':
    unitTest_InputReader()