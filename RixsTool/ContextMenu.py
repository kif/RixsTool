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

__doc__ = """
"""

class AbstractContextMenu(qt.QMenu):
    __doc__ = """Base class for context menus"""
    def __init__(self, parent=None):
        super(AbstractContextMenu, self).__init__()
        self.actionList = []

    def build(self):
        """
        Adds the actions in actionList to the context menu. String '<sep>' in actionList indicates a seperator.

        Elements in actionList must be either:
        - str: indicates separator
        - QAction
        - 3-Tuple: (text, QObject receiver, str member)
        """
        self.clear()
        for action in self.actionList:
            if isinstance(action, str):
                self.addSeparator()
            elif isinstance(action, tuple):
                text = action[0]
                receiver = action[1]
                function = action[2]
                self.addAction(text, receiver, function)
            elif isinstance(action, qt.QAction):
                self.addAction(action)
            else:
                raise ValueError("ProjectContextMenu.build -- unknown type '%s' in actionList"%str(type(action)))

class ItemContextMenu(AbstractContextMenu):
    def __init__(self, parent=None):
        super(ItemContextMenu, self).__init__(parent)

        showAction =  qt.QAction(
            'Show item in native format',
            self
        )
        #showAction.triggered[()].connect(project.showItem)

        removeAction = qt.QAction(
            qt.QIcon(':/icons/minus.ico'),
            'Remove item from project',
            self
        )
        #removeAction.triggered[()].connect(project.removeItem)

        self.actionList = [
            showAction,
            removeAction
        ]

class ContainerContextMenu(AbstractContextMenu):
    def __init__(self, parent=None):
        super(ContainerContextMenu, self).__init__(parent)

        renameGroupAction =  qt.QAction(
            'Rename group',
            self
        )
        #renameGroupAction.triggered[()].connect(project.renameGroup)

        removeGroupAction =  qt.QAction(
            qt.QIcon(':/icons/minus.ico'),
            'Remove group',
            self
        )
        #removeGroupAction.triggered[()].connect(project.removeGroup)

        self.actionList = [
            renameGroupAction,
            removeGroupAction
        ]

if __name__ == '__main__':
    pass