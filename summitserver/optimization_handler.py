"""
Module represents an optimization request handler.
"""

import logging

from typing import Optional, Union, Any
from collections.abc import Iterator

from summit.domain import (
    Domain,
    ContinuousVariable,
)
from summit.utils.dataset import DataSet
from summit.strategies.base import Strategy

from .constants import ALGORITHMS_MAPPING


DATA = 'DATA' # metadata for physical data in summit DataSet
# Keys for json communication
N_BATCHES = 'n_batches'
N_RETURNS = 'n_returns'
PARAMETERS = 'parameters'
RESULT = 'result'
BATCH_SIZE = 'batch_size'


def to_dataset(data: dict) -> DataSet:
    """ Build SUMMIT DataSet object from parameter dictionary.

    SUMMIT DataSet is a custom wrapper over pandas DataFrame, containing
    columns metadata. Custom constructor needed.

    Args:
        data (Dict): parameter and target dictionary, as received from the
            optimizer client.

    Returns:
        :obj:DataSet: SUMMIT dataset.
    """
    # "Unpacking"
    n_batches: int = data[N_BATCHES] # Number of last experiments
    parameters: dict = data[PARAMETERS]
    results: dict = data[RESULT]
    # Special case to pick all experiments
    if n_batches == -1:
        n_batches = 0
    # Creating an index list for picking certain parameters/results
    # From an array of the first result in recorded results
    first_result = results[list(results)[0]]
    idx_list = list(range(len(first_result)))
    # Building dictionaries for dataset
    dss = []
    # Iterating over an array of results for the first result
    # In reverse order, assuming latest experiments are always appended
    for idx in idx_list[-n_batches:]:
        # Appending parameters metadata
        ds = {(key, DATA): values[idx] for key, values in parameters.items()}
        # Appending result metadata
        ds.update({(key, DATA): values[idx] for key, values in results.items()})
        dss.append(ds)

    ds = DataSet(dss, columns=[key[0] for key in ds])

    return ds

class OptimizationHandler:

    def __init__(self, init_request: dict) -> None:
        """ Handler class to process optimization requests. """

        self.proc_hash: str = init_request['hash']

        self.algorithm_props: dict = init_request['algorithm']

        self.domain: Domain = Domain()

        self.batch_size: int = 1

        self.strategy: Optional[dict] = None

        self.suggestions: Iterator = iter([])

        # placeholder for the last suggested experiments
        self.prev_suggestion: DataSet = DataSet()

        self.last_results: Optional[DataSet] = None

        # registering logger
        self.logger: logging.Logger = logging.getLogger(
            f'summit-server.optimization-handler-{self.proc_hash[:6]}')

    def _build_domain(
        self,
        parameters: dict[str, Union[str, dict[str, Any]]]
    ) -> None:
        """ Build SUMMIT domain from given parameters dictionary.

        Args:
            parameters (Dict): Parameters for the reaction optimization.
                Should contain "parameters" dictionary with reaction variables
                and "target" dictionary for reaction targets.
        """

        # Extracting batch size depending on the parameter dictionary length
        self.batch_size = parameters[BATCH_SIZE]

        # Assuming "batch 1" is always present
        # And the parameters are the same across batches
        for key, value in parameters[PARAMETERS]['batch 1'].items():
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

        self.logger.debug('Built Domain: %s', self.domain.to_dict())

    def build_strategy(self) -> None:
        """ Build SUMMIT strategy from the given method dictionary. """

        strategy_name = self.algorithm_props.pop('name')
        self.strategy: Strategy = ALGORITHMS_MAPPING[strategy_name](
            domain=self.domain,
            **self.algorithm_props
        )
        self.logger.info('Registered strategy %s for <%s>.',
                         self.strategy.__class__.__name__,
                         self.proc_hash)

    def _from_dataset(self, dataset):
        """ Convert SUMMIT DataSet object to parameter dictionary.

        Args:
            dataset (:obj:Dataset): SUMMIT DataSet containing information about
                experiment setup.

        Returns:
            Dict: experiment setup dictionary, as sent to the optimizer client.
        """

    def query_next_experiment(self) -> dict[str, dict[str, float]]:
        """ Calls the strategy for the new parameter set.

        Returns:
            dict[str, dict[str, float]]: Nested dictionary with the next
                experiment parameters, batch-wise.
        """

        # Building next experiment dictionary
        next_experiment = {}
        batch_id = 0
        while batch_id != self.batch_size:
            try:
                # Will return a tuple from DataFrame as (ROW_ID, VALUE)
                suggestion = next(self.suggestions)
                self.logger.debug('Yielding suggestion from suggestion pool.')

            except StopIteration:
                self.logger.debug('No more suggestion in pool, querying.')
                self.logger.debug('Using previous results as\n%r',
                                  self.last_results)
                try:
                    suggestion = self.strategy.suggest_experiments(
                        num_experiments=self.batch_size,
                        prev_res=self.last_results
                    )

                except ValueError:
                    # Special case for the NelderMead simplex if using
                    # Previous data -> just skip it
                    suggestion = self.strategy.suggest_experiments()
                except Exception as e:
                    self.logger.exception('Exception while running the\
optimization strategy')
                    raise e

                self.logger.info('Obtained new suggestion from strategy:\n%r',
                                suggestion)
                # since not all strategies return single suggestion
                # even when just one was requested
                # the iterator is used
                self.suggestions = suggestion.iterrows()

                continue

            # Advancing
            batch_id += 1

            next_experiment.update({f'batch {batch_id}': {
                    variable.name: suggestion[1][variable.name][0]
                    for variable in self.domain.variables
                    if not variable.is_objective
                }})

        return next_experiment

    def register_result(self, request: dict) -> None:
        """ Register last result from the client request. """

        if self.last_results is None:
            # initial record
            self.logger.debug('Registering initial result from %s', request)
            self.last_results = to_dataset(request)

        # TODO check which algorithms do not store information inside
        # And therefore require full results list when querying for the next
        # Parameter setup
        elif len(self.last_results) == len(self.prev_suggestion):
            # last result should always match
            # the dimension of previously suggested experiment DataSet
            self.last_results = self.last_results.append(
                to_dataset(request),
                ignore_index=True
            )

        else:
            self.logger.debug('New last result from %s', request)
            self.last_results = to_dataset(request)

    def __call__(self, request: dict) -> dict[str, dict[str, float]]:
        """ Main call to handle request.

        Builds the strategy and domain; registering the result and returns
        next experimental parameters if requested.
        """
        if self.strategy is None:
            self._build_domain(request)
            self.build_strategy()
            return {'strategy': self.strategy.to_dict()}

        if 'result' in request:
            self.register_result(request)

        self.batch_size = request.get(N_RETURNS, self.batch_size)

        next_experiment = self.query_next_experiment()
        # appending strategy for client backup
        # next_experiment.update(strategy=self.strategy.to_dict())
        return next_experiment
