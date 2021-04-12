#Calls of imported functions shall be in the callgraph, but not their imports
import os
import numpy as np
from PIL import Image as img
from re import match

def a2():
    b2()
    callsFiveFunctions()


def b2():
    return


def callsFiveFunctions():
    os.mkdir('ShallBeInCallgraph')
    img.open('ShallBeInCallgraph')
    np.array(['ShallBeInCallgraph'])
    match('ShallBeInCallgraph', '')
    os.path.join('NeedNotBe', 'AssignedToNamespace')
    return


#It is expected that modules do not make function calls upon import
os.mkdir('NeedNotBeInCallgraph')