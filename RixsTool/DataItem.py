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

DEBUG = 1

class DataItem(object):
    __doc__ = """Generic class to contain data"""
    interpretation = 'Dataset'

    def __init__(self, key, header, array, fileLocation):
        super(DataItem, self).__init__()
        self._key = key
        self.header = header
        self.array = array
        self.fileLocation = fileLocation
        self.__identifier = uuid4()

    def __repr__(self):
        return '%s: %s %s' % (self.key(), str(self.shape()), type(self.array))

    def key(self):
        return self._key

    def description(self):
        return self.interpretation

    def shape(self):
        return self.array.shape

    def dtype(self):
        return self.array.dtype

    def getID(self):
        return self.__identifier

    def hdf5Dump(self):
        raise NotImplementedError('DataItem.hdfDump -- to be implemented here?')

class ScanItem(DataItem):
    __doc__ = """Class to contain data in multiple 1D numpy arrays"""
    interpretation = 'Scan'
    pass

class SpecItem(DataItem):
    __doc__ = """Class to contain data in 1D numpy array"""
    interpretation = 'Spec'
    pass

class ImageItem(DataItem):
    __doc__ = """Class to contain data in 2D numpy array"""
    interpretation = 'Image'
    pass

class StackItem(DataItem):
    __doc__ = """Class to contain data in 3D numpy array"""
    interpretation = 'Stack'
    pass