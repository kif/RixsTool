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
from collections import defaultdict
import numpy as np
import time

flatten = lambda llist: sum(llist, [])

class InputReader(object):
    def __init__(self):
        object.__init__(self)
        self.__fileList = []
        self.__fileDict = {}
        self._srcType = None
        # Meta
        # Data
        # - x
        # - y
        # - ScanNo
        # Pos
        # - Motornamen
        # - FileName
        # - ScanNo
        self.refreshing = False
        self._data = {
            'FileLocations': [],
            'numImages': [],
            'Headers': [],
            'Images': np.ndarray((0,0,0), dtype=int)
        }

    def __getitem__(self, key):
        '''
        Returns a list of the property <key> stored in the self.__data dictionary.
        The order of the elements is that same as the order of self.__fileList, i.e.
        the order in which the data was added.
        '''
        return self._data[key]

    def __readFiles(self, llist):
        if isinstance(self._srcType, type(None)):
            raise NotImplementedError('Do not instantiate base class')
        for filename in llist:
            print('InputReader.__readFiles -- reading:',filename)
            if not OsAccess(filename, OS_R_OK):
                print("Invalid file '%s'"%filename)
            tmp = self._srcType(filename)
            path, key = OsPathSplit(filename)
            if len(key) == 0:
                print('readFiles -- len(key) == 0, This should not happen!')
                self.__fileList = []
                self.__fileDict = {}
                return  False
            self.__fileList.append(key)
            self.__fileDict[key] = tmp
        return True

    def _setData(self):
        '''
        Fills the self.__data dictionary with the corresponding values. This
        funtion needs to be reimplemented in every inherited class.
        '''
        raise NotImplementedError('Do not instantiate base class')

    def getFileList(self):
        return self.__fileList

    def getFileDict(self):
        return self.__fileDict

    def keys(self):
        return self._data.keys()

    def getData(self):
        return self._data

    def refresh(self, llist=None):
        '''
        :param llist: List of files to refresh
        :type llist: list
        '''
        self.refreshing = True
        if llist is None:
            llist = self.__fileList
        self.__readFiles(llist)
        self._setData()
        self.refreshing = False

class EdfInputReader(InputReader):
    def __init__(self):
        InputReader.__init__(self)
        self._srcType = EdfFile

    def _setData(self):
        timeStart = time.time()
        edfDict = self.getFileDict()
        # Respect the order of self.__fileDict
        keyList = self.getFileList()
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
        print('EdfInputReader._setData -- Method finished in %.3f s',
              timeEnd - timeStart)

    def getMotorPositions(self, key=None):
        '''
        :param key: Name of header item
        :type key: str
        :param idx: idx-th scan in self.__fileList
        :type idx: int
        '''
        # Collect all motor names
        motorNames = set()
        for elem in flatten(self.getHeaderItem('motor_mne', key)):
            motorNames.update(elem.split())
        # Collect all motor positions
        ret = []
        for cnt, key in enumerate(self.getFileList()):
            scans = []
            ddict = defaultdict(list)
            # Generate name/pos ddict
            for name, pos in zip(self.getHeaderItem('motor_mne', cnt),
                                 self.getHeaderItem('motor_pos', cnt)):
                namesTmp = name.split()
                posTmp = pos.split()
                scans.append(dict(zip(namesTmp, posTmp)))
            for motorDict in scans:
                for name in motorNames:
                    value = float(motorDict.get(name, 'NaN'))
                    ddict[name].append(value)
            ret.append(ddict)
        #for elem in :
        return ret

    def getHeaderItem(self, key, idx=None, default=None):
        '''
        :param key: Name of header item
        :type key: str
        :param idx: idx-th scan in self.__fileList
        :type idx: int
        '''
        # Works only if header is dictionary
        headers = self._data['Headers']
        llist = []
        if idx is not None:
            header = headers[idx]
            for elem in header:
                llist.append(elem.get(key, default))
        else:
            for header in headers:
                for elem in range(len(header)):
                    tmp = []
                    try:
                        tmp.append(header[elem][key])
                    except KeyError:
                        tmp.append(default)
                    llist.append(tmp)
            if len(llist) == 0:
                llist = None
        return llist


if __name__ == '__main__':
    rixsImageDir = 'C:\\Users\\tonn\\lab\\rixs\\Images'
    from os import listdir as OsListDir
    from os.path import isfile as OsPathIsFile, join as OsPathJoin
    imageList = [OsPathJoin(rixsImageDir,fn) for fn in OsListDir(rixsImageDir)\
                 if OsPathIsFile(OsPathJoin(rixsImageDir,fn))]

    a = EdfInputReader()
    a.refresh(imageList)
    print(a)