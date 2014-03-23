#/*##########################################################################
# Copyright (C) 2004-2014 European Synchrotron Radiation Facility
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
from os.path import split as OsPathSplit
from os import access as OsAccess
from os import R_OK as OS_R_OK
import numpy as np
import time
import re
from RixsTool.DataItem import ImageItem, StackItem

__doc__ = '''
ImageReader interface:
__getitem__(idx):
    idx is string -> returns all data stored under 'FileLocation', 'Headers', 'Images', ...
    idx is int -> returns all of the above for a certain key in self.__fileList
len() -> Returns number of files
getFileDict() -> Returns dictionary of the low-level input readers (EDFFile, raw, ...)
keys() -> Returns the handles which identify a reader
items() -> Returns ['FileLocations', 'numImages', 'Headers', 'Images'], i.e. the self._data headers
getData() -> Returns all the date (i.e. keys, header, images, ...)
def append(llist) -> Adds lo cations in llist to fileList
def appendFilename(name) -> Same as above, but for single string
refresh(llist=None) -> Reads all the files
'''

class ImageReader(object):
    def __init__(self):
        object.__init__(self)
        self.__fileList = []
        self.__fileDict = {}
        self._srcType = None
        self.refreshing = False
        self._data = {
            'FileLocations': [],
            'numImages': [],
            'Headers': [],
            'Images': np.ndarray((0,0,0), dtype=int)
        }
        self._items = []

    def __getitem__(self, idx):
        """
        :param idx: Either the index of an image in self.__fileList or a key from ImageReader.keys()
        :type idx: int or str

        idx is int:
        Returns a tupel containing the corresponding
        (filename, header, image, file location, numberOfImages)

        idx is str:
        Returns a list of the property <key> stored in the self._data dictionary.
        The order of the elements is that same as the order of self.__fileList, i.e.
        the order in which the data was added.
        """
        if isinstance(idx, str):
            return self._data[idx]
        elif isinstance(idx, int):
            if idx >= len(self):
                raise IndexError('ImageReader index %d out of range(%d)'%(idx, len(self)))
            key = self.__fileList[idx]
            numImages = self._data['numImages'][idx]
            data = (key,
                    self._data['Headers'][idx],
                    self._data['Images'][idx],
                    self._data['numImages'][idx],
                    self._data['FileLocations'][idx])
            if numImages > 1:
                data = StackItem(
                    key=key,
                    header=self._data['Headers'][idx],
                    array=self._data['Images'][idx],
                    fileLocation=self._data['FileLocations'][idx]
                )
            else:
                data = ImageItem(
                    key=key,
                    header=self._data['Headers'][idx],
                    array=np.squeeze(self._data['Images'][idx]),
                    fileLocation=self._data['FileLocations'][idx]
                )
            return data
        else:
            raise TypeError('ImageReader indices must be integers or keys')

    def __len__(self):
        return len(self.__fileList)

    def __repr__(self):
        all = [self.__getitem__(idx) for idx in range(len(self))]
        inputType = str(self._srcType)
        return '\n\t'.join(['%s %s %s'%(inputType,'instance at',id(self))]+\
                           ['%s -> %d Image(s)'%(key, numImages) for key, header, image, numImages, loc in all])

    def __readFiles(self, llist):
        if isinstance(self._srcType, type(None)):
            raise NotImplementedError('Do not instantiate base class')
        for filename in llist:
            print('ImageReader.__readFiles -- reading:',filename)
            if not OsAccess(filename, OS_R_OK):
                print("Invalid file '%s'"%filename)
                continue
            tmp = self._srcType(filename)
            path, key = OsPathSplit(filename)
            if len(key) == 0:
                print('readFiles -- len(key) == 0, This should not happen!')
                self.__fileList = []
                self.__fileDict = {}
                return  False
            if key not in self.__fileList:
                self.__fileList.append(key)
            self.__fileDict[key] = tmp
        return True

    def _setData(self, llist):
        """
        Fills the self.__data dictionary with the corresponding values. This
        funtion needs to be reimplemented in every subclass.
        """
        raise NotImplementedError('Do not instantiate base class')

    def getFileDict(self):
        return self.__fileDict

    def keys(self):
        return self.__fileList

    def items(self):
        return self._data.keys()

    def getData(self):
        return self._data

    def appendFilename(self, name):
        self.__fileList.append(name)

    def append(self, llist):
        """
        :param llist: List of files to append
        :type llist: list

        Appends new files to self.__filelist if they
        are not already present.
        """
        self.refreshing = True
        self.__readFiles(llist)
        print('InputReader.append -- llist:',str(llist))
        self._setData(llist)
        self.refreshing = False


    def refresh(self, llist=None):
        '''
        :param llist: List of files to refresh
        :type llist: list

        # TODO: Do not add file, only refresh those given in llist!
        Reads all files stored in filelist. If the list
        parameter is provided, the existing filelist is
        overwritten.
        '''
        self.refreshing = True
        if llist is None:
            llist = self.__fileList
        print('InputReader.refresh -- llist:',str(llist))
        self.__readFiles(llist)
        self._setData(llist)
        self.refreshing = False

class RawTextInputReader(ImageReader):
    def __init__(self):
        ImageReader.__init__(self)
        self._srcType = open

    def _setData(self):
        timeStart = time.time()
        fileDict = self.getFileDict()
        # Respect the order of self.__fileDict
        keyList = self.keys()

        fileLocs = [fileDict[key].name for key in keyList]
        rawInput = [fileDict[key].read() for key in keyList]

        headers = len(keyList) * ['']
        data = len(keyList) * ['']
        # Look for header
        print('RawTextInputReader._setData -- looking for headers')
        for idx, raw in enumerate(rawInput):
            ### Assume header is enclosed in {} brackets..
            matchObj = re.match(r'\{.*\}', raw, re.DOTALL)
            if matchObj:
                headers[idx] = matchObj.group(0)
                # Remove header from raw string
                headerEnd = matchObj.end()+1
                data[idx] = raw[headerEnd:]
                print("\tAborting {} header search. Header:",headers[idx])
                continue
            ### Match all lines starting with '#'
            header = ''
            lines = raw.splitlines(keepends=True)
            for jdx, line in enumerate(lines):
                matchObj = re.match(r'^#.*', line)
                if matchObj:
                    header += matchObj.group(0)
                else:
                    # Reduce raw by header
                    data[idx] = ''.join(lines[jdx:])
                    headers[idx] = header
                    # Once a line is found that does not match
                    # the pattern, exit 'for line in ...' loop
                    print("\tAborting # header search. Header:",headers[idx])
                    break
            if len(header) > 0:
                # Header length is non-zero, something must have been
                # found, continue with next raw string
                print('\tNo header found')
                continue
            headers[idx] = ''
            data[idx] = raw

        images = len(keyList) * [np.empty(0,dtype=float)]
        # Get data: At this point it is assumed that if there was
        # a header in the raw string, it is now removed
        for idx, raw in enumerate(data):
            # Remove leading newlines/whitespaces
            tmp = raw.strip()
            numRows = len(tmp.splitlines())
            image = np.fromstring(raw, sep=' ')
            # Assume column format
            print('numRows:', numRows)
            print('len(image):', len(image))
            #image = image.reshape((len(image)/numRows, numRows))
            image = image.reshape((numRows, len(image)/numRows))
            images[idx] = image

        numImages = len(keyList) * [1]

        # Assign to self_data dictionary
        self._data['FileLocations'] = fileLocs
        self._data['numImages'] = numImages
        self._data['Headers'] = headers
        self._data['Images'] = images
        timeEnd = time.time()
        # Approx 1.5s for 17 2048x512 images. Principle part of the time
        # goes into building the array..
        print('RawTextInputReader._setData -- Method finished in %.3f s'%\
              (timeEnd - timeStart))

class EdfInputReader(ImageReader):
    def __init__(self):
        ImageReader.__init__(self)
        self._srcType = EdfFile

    def _setData(self, keyList=None):
        # def __init__(self, key, header, array, fileLocation):
        timeStart = time.time()

        #
        # Reference agains self.keys()
        #
        keys = self.keys()

        #
        # Create either ImageItem or StackItem, if single or multiple images are present
        #
        for key in keyList:
            edfReader = edfDict[key]
            numImages = edfReader.GetNumImages()



            if numImages == 1:
                item = ImageItem(
                    key=key,
                    header=edfReader.GetHeader(0),
                    array=edfReader.GetHeader(0),
                    fileLocation=edfReader.FileName
                )
            else:
                print('EDFInputReader._data -- Unsupported number of images in single EDF file')
                item = ImageItem(
                    key=key,
                    header='',
                    array=np.zeros((10, 10), dtype=np.uint16),
                    fileLocation=edfReader.FileName
                )
        timeEnd = time.time()
        print('EdfInputReader._setData -- Method finished in %.3f s'%\
              (timeEnd - timeStart))

"""
    def _setData(self, keyList):
        timeStart = time.time()
        edfDict = self.getFileDict()
        # Respect the order of self.__fileDict
        keyList = self.keys()
        fileLocs = [edfDict[key].FileName for key in keyList]
        numImages = [edfDict[key].GetNumImages() for key in keyList]
        # Make shure to loop through all scans
        allScans = list(zip(keyList,
                            [range(cnt) for cnt in numImages]))
        headers = [[edfDict[key].GetHeader(idx) for idx in rng]\
                   for key, rng in allScans]
        images = [np.array([edfDict[key].GetData(idx) for idx in rng])\
                  for key, rng in allScans]
        self._data['FileLocations'] = fileLocs
        self._data['numImages'] = numImages
        self._data['Headers'] = headers
        self._data['Images'] = images
        timeEnd = time.time()
        # Approx 1.5s for 17 2048x512 images. Principle part of the time
        # goes into building the array..
        print('EdfInputReader._setData -- Method finished in %.3f s'%\
              (timeEnd - timeStart))
"""

def run_test():
    rixsImageDir = 'C:\\Users\\tonn\\lab\\rixs\\Images'
    from os import listdir as OsListDir
    from os.path import isfile as OsPathIsFile, join as OsPathJoin
    edfImageList = [OsPathJoin(rixsImageDir,fn) for fn in OsListDir(rixsImageDir)\
                 if OsPathIsFile(OsPathJoin(rixsImageDir,fn))][1:]
    #rawImageList = ['C:\\Users\\tonn\\lab\\datasets\\EL9imageNoHeader.txt',
    #                'C:\\Users\\tonn\\lab\\datasets\\EL9imageParaHeader.txt',
    #                'C:\\Users\\tonn\\lab\\datasets\\EL9image.txt']

    edfReader = EdfInputReader()
    edfReader.refresh(edfImageList)
    #rawReader = RawTextInputReader()
    #rawReader.refresh(rawImageList)
    #return rawReader
    return edfReader

if __name__ == '__main__':
    a = run_test()
    foo = a['Images'][0]
    print('foo.shape', foo.shape)
    print(a)

    print('Done!')