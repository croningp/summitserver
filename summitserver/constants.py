""" Module constants. """

from summit.strategies.tsemo import TSEMO
from summit.strategies.sobo import SOBO
from summit.strategies.neldermead import NelderMead
from summit.strategies.snobfit import SNOBFIT
from summit.strategies.multitask import MTBO
from summit.strategies.entmoot import ENTMOOT


ALGORITHMS_MAPPING = {
    'TSEMO': TSEMO,
    'SOBO': SOBO,
    'MTBO': MTBO,
    'ENTMOOT': ENTMOOT,
    'NelderMead': NelderMead,
    'SNOBFIT': SNOBFIT,
}
