import ahu_extra1
from ahu_gen import Drawing

def build():
    d = Drawing()
    ahu_extra1.duct_details(d)
    return d
