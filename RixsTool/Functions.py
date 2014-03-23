#/*##########################################################################
# Copyright (C) 2004-2013 European Synchrotron Radiation Facility
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

import numpy
from RixsTool.Items import FunctionItem

DEBUG = 1


class Fit(object):
    @staticmethod
    def quadratic(fitvalues, x=None, key=''):
        """
        :param ndarray fitvalues: Values on which the fit is carried out
        :param ndarray x: x-range of the fitvalues (default: None)

        :raises numpy.RankWarning: In case the least squares fit is badly conditioned.
        """
        if x is None:
            x = numpy.arange(
                start=0,
                stop=len(fitvalues)
            )
        print(fitvalues)
        print(x)

        #
        # Perform fit
        #
        #par = numpy.polyfit(
        #    x=x,
        #    y=fitvalues,
        #    deg=2)
        full = numpy.polyfit(
            x=x,
            y=fitvalues,
            deg=2,
            full=True)
        par = full[0]  # Fit parameters
        fitReport = 'Residuals: %s\n' % str(full[1])
        #rank = full[2]
        #singularValues = full[3]
        #rcond = full[4]

        #
        # Instantiate FunctionItem object
        #
        function = FunctionItem(key=key, header=fitReport)

        #
        # Function definition: y = a * x**2 + b * x + c
        #
        expression = lambda x, a, b, c: a * x**2 + b * x + c
        function.setExpression(expression)

        #
        # Parameter assignment
        #
        parameters = {
            'a': par[0],
            'b': par[1],
            'c': par[2],
        }
        function.setParameters(parameters)

        if DEBUG >= 1:
            print('Fit.quadratic -- consistency check succeeded: %s' % str(function.consistencyCheck()))
            print('\ta = %.3e' % par[0])
            print('\tb = %.3e' % par[1])
            print('\tc = %.3e' % par[2])
        return function