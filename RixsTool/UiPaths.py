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

import os
import os.path

absolutePath = os.path.dirname(os.path.abspath(__file__))


class UiPaths(object):
    @staticmethod
    def abstractTitleToolBar():
        return os.path.join(absolutePath, "ui", 'abtracttitletoolbar.ui')

    @staticmethod
    def alignmentFilterUiPath():
        return os.path.join(absolutePath, "ui", 'alignmentfilter.ui')

    @staticmethod
    def bandPassFilterUiPath():
        return os.path.join(absolutePath, "ui", 'bandpassfilter.ui')

    @staticmethod
    def bandPassFilterID32UiPath():
        return os.path.join(absolutePath, "ui", 'bandpassfilterID32.ui')

    @staticmethod
    def energyAlignmentUiPath():
        return os.path.join(absolutePath, "ui", 'energyalignment.ui')

    @staticmethod
    def fileSystemBrowserUiPath():
        return os.path.join(absolutePath, "ui", 'filesystembrowser.ui')

    @staticmethod
    def mainWindowUiPath():
        return os.path.join(absolutePath, "ui", 'mainwindow_imageView.ui')

    @staticmethod
    def sumToolUiPath():
        return os.path.join(absolutePath, "ui", 'sumtool.ui')


if __name__ == '__main__':
    print(UiPaths.mainWindowUIPath())