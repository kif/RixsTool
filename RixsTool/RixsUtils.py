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

def reduce(llist):
    """
    :param llist: List of lists
    :type llist: list

    Unravels a list of lists.
    """
    return sum(llist, [])

def unique(seq, ident=''):
    """
    :param seq: Container
    :type seq: list, dict, ...
    :param ident: Name of member function or member attribute of elements in seq. Must determine the uniqueness of an element.
    :type ident: str

    In place removal of redundant elements in a sequence using the given identifier. If ident is not defined, python natively
    uses id(). Notice that if ident is a (member *, class *, or static *) method the return type of ident must be non-mutuable and
    hashable. Only parameterless functions are supported.

    Extended solution of stackoverflow user J.F. Sebastian:
    http://stackoverflow.com/questions/89178/in-python-what-is-the-fastest-algorithm-for-removing-duplicates-from-a-list-so/282589#282589
    """
    if len(seq) == 0:
        return []
    if len(ident) > 0:
        if hasattr(seq[0], ident):
            useIdent = True
        else:
            raise AttributeError('RixsUtils.unique -- %s has no attibute %s'%\
                                 (str(type(seq[0])), str(ident)))
    else:
        useIdent = False
    seen = {}
    insertPos = 0
    for item in seq:
        if useIdent:
            member = getattr(item, ident)
            if callable(member):
                key = member()
            else:
                key = member
        else:
            key = item
        if key not in seen:
            seen[key] = True
            seq[insertPos] = item
            insertPos += 1
    del seq[insertPos:]


def unitTest_unique():
    #
    # Test if unique works on list of ints
    #
    l0 = [i for i in range(10)] + [i for i in range(10)]
    l1 = l0.copy()
    unique(l1)

    print('RixsUtils.unitTest_unique -- Reducing list of ints to unique elements:')
    print('\tlen(l0):', len(l0))
    print('\tlen(l1):', len(l1))

    if len(l0) == 20 and len(l1) == 10:
        first = True
    else:
        first = False

    #
    # Test if unique works on arbitrary object (Foo class)
    #
    class Foo(object):
        def __init__(self, a):
            self.a = a

        def foo(self):
            return self.a

        @staticmethod
        def staticFoo():
            # Should be the same for class methods
            return -1

        # Not supported (yet): Functions w\ parameters
        #def fooWithArgs(self, fst, snd):
        #    return self.a


    l0 = [Foo(i) for i in range(10)] + [Foo(i) for i in range(10)]
    l1 = l0.copy()
    unique(l1)
    l2 = l0.copy()
    unique(l2, 'a')

    print('RixsUtils.unitTest_unique -- Reducing list of class Foo to unique elements:')
    print('\tlen(l0):', len(l0))
    print('\tlen(l1):', len(l1))
    print('\tlen(l2):', len(l2))

    if len(l1) == 20 and len(l2) == 10:
        second = True
    else:
        second = False

    l0 = [Foo(i) for i in range(10)] + [Foo(i) for i in range(10)]
    l1 = l0.copy()
    unique(l1)
    l2 = l0.copy()
    unique(l2, 'foo')

    print('RixsUtils.unitTest_unique -- Reducing list of class Foo to unique elements using member method:')
    print('\tlen(l0):', len(l0))
    print('\tlen(l1):', len(l1))
    print('\tlen(l2):', len(l2))

    if len(l1) == 20 and len(l2) == 10:
        third = True
    else:
        third = False

    l0 = [Foo(i) for i in range(10)] + [Foo(i) for i in range(10)]
    l1 = l0.copy()
    unique(l1)
    l2 = l0.copy()
    unique(l2, 'staticFoo')

    print('RixsUtils.unitTest_unique -- Reducing list of class Foo to unique elements static method:')
    print('\tlen(l0):', len(l0))
    print('\tlen(l1):', len(l1))
    print('\tlen(l2):', len(l2))

    if len(l1) == 20 and len(l2) == 1:
        fourth = True
    else:
        fourth = False

    if first and second and third and fourth:
        print('RixsUtils.unitTest_unique -- Success!')
        return True
    else:
        print('RixsUtils.unitTest_unique -- Failure!')
        return False

if __name__ == '__main__':
    unitTest_unique()