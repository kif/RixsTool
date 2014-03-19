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
from inspect import getargspec as getArgSpec
import numpy

DEBUG = 1


class ProjectItem(object):
    __doc__ = """Generic class to contain data"""
    interpretation = 'Abstract DataItem'

    def __init__(self, key, header):
        super(ProjectItem, self).__init__()
        self._key = key
        self.header = header
        self.__identifier = uuid4()

    def __repr__(self):
        return '%s: %s' % (self.key(), str(self.interpretation))

    def key(self):
        return self._key

    def description(self):
        return self.interpretation

    def getID(self):
        return self.__identifier

    def hdf5Dump(self):
        raise NotImplementedError('DataItem.hdfDump -- to be implemented here?')


class DataItem(ProjectItem):
    __doc__ = """Generic class to contain numeric data"""
    interpretation = 'Dataset'

    def __init__(self, key, header, array, fileLocation):
        ProjectItem.__init__(self, key, header)
        self.fileLocation = fileLocation
        self.array = array

    def __repr__(self):
        return '%s: %s %s' % (self.key(), str(self.shape()), type(self.array))

    def shape(self):
        return self.array.shape

    def dtype(self):
        return self.array.dtype


class FunctionItem(ProjectItem):
    __doc__ = """Class to contain a real valued function in terms of an analytical expression and a set of parameters"""
    interpretation = 'Function'

    def __init__(self, key, header):
        ProjectItem.__init__(self, key, header)
        self.expression = lambda x: x
        self.parameters = {}
        self._argspec = getArgSpec(self.expression)

    def setExpression(self, expression):
        """
        :param function expression: Analystical function
        """
        self._argspec = getArgSpec(expression)
        self.expression = expression

    def setParameters(self, parameters):
        """
        :param dict parameters: parameters defining the function
        """
        self.parameters = parameters

    def consistencyCheck(self):
        # TODO: Improve consistency check
        args = self._argspec.args
        keys = self.parameters.keys()

        # The following does not work, since one parameter
        # of the expression is always the xrange..
        #return args == keys
        for param in keys:
            if param not in args:
                return False
        return True

    def sample(self, sampleRange=None):
        if sampleRange is None:
            sampleRange = numpy.linspace(0, 512, 512)
        if not self.expression:
            raise AttributeError('FunctionItem.sample -- expression not initialized')
        if len(self.parameters) <= 0:
            raise AttributeError('FunctionItem.sample -- parameters dict empty')
        # CONTINUE HERE
        param = self.parameters
        param.update({'x': sampleRange})
        return self.expression(**param)


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


if __name__ == '__main__':
    __doc__ = 'Modified inheritance structure of DataItem child classes. Added FunctionItem class'
    testExpr = lambda a, x: abs(x)
    testAnaItem = FunctionItem('foo', 'header')
    testAnaItem.setExpression(testExpr)
    testAnaItem.setParameters({'a': 1.})
    print('Consistency check succeeded: %s' % str(testAnaItem.consistencyCheck()))

    print(testAnaItem.sample(numpy.linspace(-5, 5, 10)))

