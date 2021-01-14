""" Module constants. """

# from summit.strategies.tsemo import TSEMO
from summit.strategies.sobo import SOBO
from summit.strategies.neldermead import NelderMead
from summit.strategies.snobfit import SNOBFIT


ALGORITHMS_MAPPING = {
    # 'TSEMO': TSEMO,
    'SOBO': SOBO,
    'NelderMead': NelderMead,
    'SNOBFIT': SNOBFIT,
}
