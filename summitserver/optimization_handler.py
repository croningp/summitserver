"""
Module represents an optimization request handler.
"""

from summit.domain import (
    Domain,
    ContinuousVariable,
)

from .constants import ALGORITHMS_MAPPING


class OptimizationHandler:

    def __init__(self, init_request):
        """ Handler class to process optimization requests. """

        self.proc_hash = init_request['hash']

        self.algorithm_props = init_request['algorithm']

        self.domain = Domain()

        self.strategy = None

    def _build_domain(self, parameters):
        """ Build SUMMIT domain from given parameters dictionary.

        Args:
            parameters (Dict): Parameters for the reaction optimization.
                Should contain "parameters" dictionary with reaction variables
                and "target" dictionary for reaction targets.
        """

        for key, value in parameters['parameters']:
            # continuous variable, having min and max values
            if 'max_value' in value and 'min_value' in value:
                self.domain += ContinuousVariable(
                    name=key,
                    description=key,
                    bounds=[value['min_value'], value['max_vaule']],
                )

        for key, value in parameters['target']:
            self.domain += ContinuousVariable(
                name=key,
                description=key,
                bounds=[0, value],
                is_objective=True,
                maximize=True,
            )

    def build_strategy(self):
        """ Build SUMMIT strategy from the given method dictionary. """
        self.strategy = ALGORITHMS_MAPPING[self.algorithm_props.pop('name')](
            domain=self.domain,
            **self.algorithm_props
        )

    def call_strategy(self, request):
        """ Calls the strategy for the new parameter set. """


    def __call__(self, request):
        """ Main call to handle request. """
        if self.strategy is None:
            self._build_domain(request)
            self.build_strategy()
            return self.strategy.to_dict()
        return self.call_strategy(request)
