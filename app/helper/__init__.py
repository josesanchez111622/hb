import sys


def isNum(data):
    try:
        int(data)
        return True
    except:
        return False


def parseInt(a):
    try:
        if isinstance(a, int):
            return a
        return int(eval("{}".format(a)))
    except:
        print(sys.exc_info())
        return 0
