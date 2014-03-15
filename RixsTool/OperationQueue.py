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

from PyMca import PyMcaQt as qt
from RixsTool.datahandling import RixsProject
from RixsTool.Operations import Filter, Integration, Alignment


class OperationQueue(object):
    def __init__(self):
        self.__oplist = []
        self.__paramList = []

    def __len__(self):
        return len(self.__oplist)

    def process(self, data):
        for op, param in zip(self.__oplist, self.__paramList):
            data = op(data, param)
        return data

    def addOperation(self, opList, paramList=None, pos=-1):
        if pos == -1:
            pos = len(self)
        check = [(op in self.__oplist) for op in opList]
        if any(check):
            idx = check.index(True)
            opStr = str(opList[idx])
            raise ValueError("OperationQueue.addOperation -- operation '%s' (pos %d) already in use" % (opStr, idx))

        #
        # Add opList to self.__opList
        #
        headOp = self.__oplist[:pos]
        tailOp = self.__oplist[pos:]
        self.__oplist = headOp + opList + tailOp

        #
        # Add paramList to self.__paramList
        #
        headParam = self.__paramList[:pos]
        tailParam = self.__paramList[pos:]
        if paramList:
            self.__paramList = headParam + paramList + tailParam
        else:
            self.__paramList = headParam + [{}]*len(opList) + tailParam


class SlopeCorrection(OperationQueue):
    def __init__(self):
        OperationQueue.__init__(self)
        opList = [
            Filter.bandPassFilter,
            Integration.sliceAndSum,
            Alignment.fitAlignment
        ]
        paramList = [
            {'low': 100, 'high': 140},
            {'sumAxis': 1, 'binWidth': 64},
            {}
        ]
        self.addOperation(
            opList=opList,
            paramList=paramList
        )


class OperationQueueQObject(OperationQueue, qt.QObject):
    operationAddedSignal = qt.pyqtSignal()
    finishedSignal = qt.pyqtSignal()

    def addOperation(self, opList, paramList=None, pos=-1):
        OperationQueue.addOperation(self, opList, pos)
        self.operationAddedSignal.emit()

    def process(self, data):
        result = OperationQueue.process(self, data)
        self.finishedSignal.emit(result)


def unitTest_OperationQueue():
    directory = '/home/truter/lab/mock_folder'  # On linkarkouli

    ops = SlopeCorrection()

    proj = RixsProject()
    proj.crawl(directory)

    key = 'LBCO0483.edf'
    item = proj[key].item()

    res = ops.process(item.array)
    print(res)

    from matplotlib import pyplot as plt
    #plt.imshow(res)
    plt.plot(res)
    plt.show()


if __name__ == '__main__':
    unitTest_OperationQueue()