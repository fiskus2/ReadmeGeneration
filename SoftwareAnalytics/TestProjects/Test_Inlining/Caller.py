from CalleeFunctional import calleeF1
from CalleeObjectOriented import CalleeClass

def caller():
    '''
    bla
    :return:
    '''
    callerVar = 'text'
    calleeF1()

    instance = CalleeClass()

    if True:
        callerVar = instance.calleeC1()