import numpy as np

def minmax(x, skipna=True):
    if skipna:
        return (np.nanmin(x), np.nanmax(x))
    else:
        return (np.min(x), np.max(x))

def testbit(v, pos):
    m = 1<<pos
    return (val&m)

def setbit(v, pos):
    m = 1<<pos
    return (v|m)

def clearbit(v, pos):
    m = ~(1<<pos)
    return (v&m)

def togglebit(v, pos):
    m = 1<<pos
    return (v^m)

def popcount32(v):
    v = v - ((v >> 1) & 0x55555555)
    v = (v & 0x33333333) + ((v >> 2) & 0x33333333)
    return (((v + (v >> 4) & 0xF0F0F0F) * 0x1010101) & 0xffffffff) >> 24

def popcount64(v):
    v = v - ((v >> 1) & 0x5555555555555555)
    v = (v & 0x3333333333333333) + ((v >> 2) & 0x3333333333333333)
    return (((v + (v >> 4) & 0x0f0f0f0f0f0f0f0f) * 0x0101010101010101) & 0xffffffffffffffff) >>  56

def countbits(v, maxbits=32):
    return popcount32(v) if maxbits<=32 else popcount64(v)


        
    
