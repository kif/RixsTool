def unique(seq, ident=''):
    """
    :param seq: Container
    :type seq: list, dict, ...
    :param ident: Name of member function or member attribute of elements in seq. Must determine the uniqueness of an element.
    :type ident: str

    In place removal of redundant elements in a sequence using the given identifier. If ident is not defined, python natively
    uses id().

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
            key = getattr(item, ident)
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
    # Test if unique works on arbitrary object
    #
    class Foo(object):
        def __init__(self, a):
            self.a = a
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

    if first and second:
        print('RixsUtils.unitTest_unique -- Success!')
        return True
    else:
        print('RixsUtils.unitTest_unique -- Failure!')
        return False

if __name__ == '__main__':
    unitTest_unique()
