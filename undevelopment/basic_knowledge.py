#链式调用
#ixNetwork.Traffic.StopStatelessTrafficBlocking()

class  Caculator:

    def __init__(self):
        self._value = 10

    @property
    def add(self):
        self._value += self._value
        print(self._value)
        return self

    @property
    def multiple(self):
        self._value *= self._value
        print(self._value)
        return self
    @property
    def division(self):
        self._value /= self._value
        print(self._value)
        return self

    @property       #方法作为类的属性
    def subtract(self):
        self._value -= self._value
        print(self._value)
        return self

    def __call__(self, *args, **kwargs):   #对象()，会调用这个方法
        return self

A=Caculator()
A.add.multiple.add.add.division.subtract()



#re.sub
import re


#反射器
CTYPE_MAP = {
    "tenFortyHundredGigLan": "TenFortyHundredGigLan",
    "novusHundredGigLan": "NovusHundredGigLan",
    "novus5GTenTwentyFiveGigLan": "Novus5GTenTwentyFiveGigLan",
    "uhdOneHundredGigLan": "UhdOneHundredGigLan",
    "aresOneFourHundredGigLan": "AresOneFourHundredGigLan",
    "aresOneEightHundredGigLanQddC": "AresOneEightHundredGigLanQddC",
    "aresOne1600G": "AresOne1600G",
}


def get_l1(vport):
    ctype = vport.L1Config.CurrentType
    prop = CTYPE_MAP.get(ctype, ctype)
    return getattr(vport.L1Config, prop)


