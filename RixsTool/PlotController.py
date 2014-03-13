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
__author__ = "V.A. Sole - ESRF Software Group"
__doc__ = """
This window handles plugins and adds a toolbar to the PlotWidget.

Currently the only dependency on PyMca is through the Icons.

"""
from PyMca import PyMcaQt as qt
from PyMca.ScanWindow import ScanWindow


class RixsPlotWindow(ScanWindow):
    def addDataItem(self, item, legend=None, info=None,
                    replot=True, replace=False, **kw):
        raise NotImplementedError('RixsPlotWindow.addDataItem -- Check if necessary!')



if __name__ == '__main__':
    app = qt.QApplication([])
    win = RixsPlotWindow()
    win.show()
    app.exec_()