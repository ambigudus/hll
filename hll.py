"""
This module implements probabilistic data structure which is able to calculate the cardinality of large multisets in a single pass using little auxiliary memory
"""
import numpy as np
import math
from hashlib import sha1
from const import rawEstimateData, biasData, tresholdData

def bit_length(w):
    return len(bin(w)) - 2 if w > 0 else 0

def get_treshold(p):
    return tresholdData[p - 4]


def estimate_bias(E, p):
    bias_vector = biasData[p - 4]
    nearest_neighbors = get_nearest_neighbors(E, rawEstimateData[p - 4])
    return sum([float(bias_vector[i]) for i in nearest_neighbors]) / len(nearest_neighbors)


def get_nearest_neighbors(E, estimate_vector):
    distance_map = [((E - float(val)) ** 2, idx) for idx, val in enumerate(estimate_vector)]
    distance_map.sort()
    return [idx for dist, idx in distance_map[:6]]


def get_alpha(p):
    if not (4 <= p <= 16):
        raise ValueError("p=%d should be in range [4 : 16]" % p)

    if p == 4:
        return 0.673

    if p == 5:
        return 0.697

    if p == 6:
        return 0.709

    return 0.7213 / (1.0 + 1.079 / (1 << p))


def get_rho(w, max_width):
    rho = max_width - bit_length(w) + 1

    if rho <= 0:
        raise ValueError('w overflow')

    return rho


class HyperLogLog(object):
    """
    HyperLogLog cardinality counter
    """

    __slots__ = ('alpha', 'p', 'm', 'M')

    def __init__(self, error_rate):
        """
        Implementes a HyperLogLog

        error_rate = abs_err / cardinality
        """

        if not (0 < error_rate < 1):
            raise ValueError("Error_Rate must be between 0 and 1.")

        # error_rate = 1.04 / sqrt(m)
        # m = 2 ** p
        # M(1)... M(m) = 0

        p = int(math.ceil(math.log((1.04 / error_rate) ** 2, 2)))

        self.alpha = get_alpha(p)
        self.p = p
        self.m = 1 << p
        self.M = [0 for i in range(self.m)]

    def __getstate__(self):
        return dict([x, getattr(self, x)] for x in self.__slots__)

    def __setstate__(self, d):
        for key in d:
            setattr(self, key, d[key])

    def add(self, value):
        """
        Adds the item to the HyperLogLog
        """
        # h: D -> {0,1} ** 64
        # x = h(v)
        # j = <x_0x_1..x_{p-1}>
        # w = <x_{p}x_{p+1}..>
        # M[j] = max(M[j], rho(w))

        x = int(sha1(bytes(value.encode('utf8') if isinstance(value, str) else value)).hexdigest()[:16], 16)
        j = x % self.m # x & (self.m - 1) # j = pnp.mod(x, self.m)
        w = x // self.m # x >> self.p #  w = pnp.floor_divide(x, self.m)

        self.M[j] = max(self.M[j], get_rho(w, 64 - self.p))
    '''
    def update(self, *others):
        """
        Merge other counters
        """

        for item in others:
            if self.m != item.m:
                raise ValueError('Counters precisions should be equal')

        self.M = [max(*items) for items in zip(*([ item.M for item in others ] + [self.M]))]
    '''
    def __eq__(self, other):
        if self.m != other.m:
            raise ValueError('Counters precisions should be equal')

        return self.M == other.M

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return round(self.card())

    def _Ep(self):
        E = self.alpha * float(self.m ** 2) / sum(math.pow(2.0, -x) for x in self.M)
        return (E - estimate_bias(E, self.p)) if E <= 5 * self.m else E

    def card(self):
        """
        Returns the estimate of the cardinality
        """
        '''
        #count number or registers equal to 0
        V = self.M.count(0)

        if V > 0:
            H = self.m * math.log(self.m / float(V))
            return H if H <= get_treshold(self.p) else self._Ep()
        else:
        '''
        return self._Ep()

x = np.random.randint(2**16, size=60000)
hll = HyperLogLog(0.01)
len1 = len(set(x))
for i in range(60000):
    hll.add(x[i])

print(len1, hll.card())