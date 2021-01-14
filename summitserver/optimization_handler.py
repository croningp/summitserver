"""
Module represents an optimization request handler.
"""

import logging

from summit.domain import (
    Domain,
    ContinuousVariable,
)
from summit.utils.dataset import DataSet

from .constants import ALGORITHMS_MAPPING


DATA = 'DATA' # metadata for physical data in summit DataSet

def to_dataset(data):
    """ Build SUMMIT DataSet object from parameter dictionary.

    SUMMIT DataSet is a custom wrapper over pandas DataFrame, containing
    columns metadata. Custom constructor needed.

    Args:
        data (Dict): parameter and target dictionary, as received from the
            optimizer client.

    Returns:
        :obj:DataSet: SUMMIT dataset.
    """
    # appending parameters metadata
    ds = {(key, DATA): value for key, value in data['parameters'].items()}
    # appending result metadata
    ds.update({(key, DATA): value for key, value in data['result'].items()})

    ds = DataSet([ds], columns=[key[0] for key in ds])

    return ds

class OptimizationHandler:

    def __init__(self, init_request):
        """ Handler class to process optimization requests. """

        self.proc_hash = init_request['hash']

        self.algorithm_props = init_request['algorithm']

        self.domain = Domain()

        self.strategy = None

        self.suggestions = iter([])

        self.last_results = None

        # registering logger
        self.logger = logging.getLogger(
            f'summit-server.optimization-handler-{self.proc_hash}')

    def _build_domain(self, parameters):
        """ Build SUMMIT domain from given parameters dictionary.

        Args:
            parameters (Dict): Parameters for the reaction optimization.
                Should contain "parameters" dictionary with reaction variables
                and "target" dictionary for reaction targets.
        """

        for key, value in parameters['parameters'].items():
            # continuous variable, having min and max values
            if 'max_value' in value and 'min_value' in value:
                self.domain += ContinuousVariable(
                    name=key,
                    description=key,
                    bounds=[value['min_value'], value['max_value']],
                )

        for key, value in parameters['target'].items():
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

    def _from_dataset(self, dataset):
        """ Convert SUMMIT DataSet object to parameter dictionary.

        Args:
            dataset (:obj:Dataset): SUMMIT DataSet containing information about
                experiment setup.

        Returns:
            Dict: experiment setup dictionary, as sent to the optimizer client.
        """

    def query_next_experiment(self):
        """ Calls the strategy for the new parameter set. """
        while True:
            try:
                # will return a tuple from DataFrame as (ROW_ID, VALUE)
                suggestion = next(self.suggestions)
                return {
                    variable.name: suggestion[1][variable.name][0]
                    for variable in self.domain.variables
                    if not variable.is_objective
                }
            except StopIteration:
                # not all strategies require num_experiments positional argument
                try:
                    suggestion = self.strategy.suggest_experiments()
                except TypeError:
                    suggestion = self.strategy.suggest_experiments(
                        num_experiments=1)
                # since not all strategies return single suggestion
                # even when just one was requested
                # the iterator is used
                self.suggestions = suggestion.iterrows()

    def register_result(self, request):
        """ Register last result from the client request. """

        if self.last_results is None:
            self.last_results = DataSet()

    def __call__(self, request):
        """ Main call to handle request. """
        if self.strategy is None:
            self._build_domain(request)
            self.build_strategy()
            return self.strategy.to_dict()
        return self.query_next_experiment()
