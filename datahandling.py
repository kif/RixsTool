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
from PyMca import PyMcaQt as qt

class DataHandler(qt.QObject):
    sigRefresh = qt.pyqtSignal(str, int)

    def __init__(self, reader, parent=None):
        qt.QObject.__init__(self, parent)
        self.db = reader
        self.getStatistics()

    def __len__(self):
        return len(self.db)

    def _handleSigScalarUpdate(self, ddict):
        print('DataHandler._handleSigScalarUpdate -- ddict:',ddict)

    def ready(self):
        return not self.db.refreshing

    def getStatistics(self):
        if not self.ready():
            print('DataHandler.getStatistics -- not ready')
        for idx, key in enumerate(self.db.keys()):
            numImages = self.db['numImages'][idx]
            imageBlob = self.db['Images']
            for jdx in range(numImages):
                image = imageBlob[jdx]
                stats = Stats2D(key, jdx, self)
                self.sigRefresh.connect(stats.refresh)
                stats.sigScalarUpdate.connect(
                            self._handleSigScalarUpdate)
                stats.basics(image)
        return True