from BaseClass import baseClass

class InheritingClass(baseClass):

    def __init__(self):
        print('something')

    def a2(self):
        self.b2()
        self.baseMethod()
        self.overriddenMethod()

    def b2(self):
        return

    def overriddenMethod(self):
        return