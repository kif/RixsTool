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

DEBUG = 1

class RixsProject(object):

    __OPERATION = 'operation'

    __DATA_TYPE = 'data' # -> 1d, 2d or 3d numpy array
    __EDF_TYPE = 'edf'   # -> Wrapper for spec files
    __RAW_TYPE = 'raw'   # -> Wrapper for plaintext data

    # TODO: Use these type too
    __SPEC_TYPE = 'spec' # -> Wrapper for spec files
    __STACK_TYPE = 'stack' # -> Wrapper for spec files

    typeList = [__SPEC_TYPE, __EDF_TYPE, __RAW_TYPE]

    def __init__(self):
        super(RixsProject, self).__init__()

        #
        # Spec readers
        #
        # TODO: Have readers for specfiles..
        self.specReaders = {
            self.__SPEC_TYPE : None
        }

        #
        # Image readers
        #
        self.imageReaders = {
            self.__EDF_TYPE : IO.EdfInputReader(),
            self.__RAW_TYPE : IO.RawTextInputReader()
        }

    def imagify(self, llist):
        """
        :param llist: List of 2D numpy arrays
        """
        raise NotImplementedError('RixsProject.imagify -- ...to be implemented')

    def image(self, key, imageType):
        """
        :param key: Identifier of the image
        :type key: str
        :param imageType: Describtor of image type (edf, raw, ...)
        :type imageType: str

        Image -> 2D numpy array

        Returns image from the data structure
        """
        reader = self.imageReaders.get(imageType, None)
        if reader is None:
            raise ValueError("RixsProject.image -- Unknown image type '%s'"%imageType)
        # User reader interface
        keys = reader.keys()
        if key not in keys:
            raise KeyError("RixsProject.image -- Key '%s' not found"%key)
        idx = keys.index(key)
        key, \
        header, \
        image, \
        numImages, \
        fileLoc = reader[idx]
        if numImages > 1:
            print("RixsProject.image -- Image '%s' is a stack!"%key)
        return image

    def readImage(self, filename, fileType):
        return self.readImages([filename], fileType)

    def readImages(self, filelist, fileType):
        try:
            reader = self.imageReaders[fileType]
        except KeyError:
            raise ValueError("RixsProject.readImages -- Unknown image Type '%s'"%fileType)
            #return False
        reader.refresh(filelist)
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

if __name__ == '__main__':
    unitTest_QDirListModel()
    #rixsImageDir = 'C:\\Users\\tonn\\lab\\rixs\\Images'
    #proj = RixsProject()
    #edfImageList = [OsPathJoin(rixsImageDir,fn) for fn in OsListDir(rixsImageDir)\
    #             if OsPathIsFile(OsPathJoin(rixsImageDir,fn))][1:]
    #proj.readImages(edfImageList, 'edf')