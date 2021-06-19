import InheritingClass as cl2

class Class1:

    def a1(self):

        somevar = 'test'
        self.b1()

        obj = cl2.InheritingClass()
        obj.a2()
        obj.overriddenMethod()

    def b1(self):
        return
