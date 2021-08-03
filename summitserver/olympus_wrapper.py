"""
Module represents an optimization request handler.
"""
import logging
from typing import Union, Any
from olympus import ParameterSpace, Parameter
from olympus import Planner, Observations

#from .constants import ALGORITHMS_MAPPING


DATA = 'DATA' # metadata for physical data in summit DataSet
# Keys for json communication
N_BATCHES = 'n_batches'
N_RETURNS = 'n_returns'
PARAMETERS = 'parameters'
RESULT = 'result'
BATCH_SIZE = 'batch_size'

class OlympusWrapper:

    def __init__(self, init_request):
        """
        Wrapper to process optimization requests for Olympus.
        Available algorithms accessible via algorithm probs kwargs:
        BasinHopping, Cma, ConjugateGradient, DifferentialEvolution,
        Genetic, Gpyopt, Grid, Hyperopt, LatinHypercube, Lbfgs,
        ParticleSwarms, Phoenics, RandomSearch, Simplex, Slsqp,
        Snobfit, Sobol, SteepestDescent.
        """

        self.proc_hash = init_request['hash']

        self.algorithm_props = init_request['algorithm']
        planner_name = self.algorithm_props.pop("name")
        self.algorithm_props.update({"kind":planner_name})

        self.param_space = ParameterSpace()

        self.observations = Observations()

        self.planner = None

        self.suggestion = None

        self.batch_size: int = 1

        # registering logger
        self.logger: logging.Logger = logging.getLogger(
            f'olympus-wrapper.optimization-handler-{self.proc_hash[:6]}')


    def build_paramspace(self, request) -> None:
        """
        Build Olympus.ParameterSpace.

        Args:
            data (Nested Dict)    Optimizer data
        """
        self.batch_size = request[BATCH_SIZE]

        for param, bounds in request[PARAMETERS]['batch 1'].items():

            low = bounds["min_value"]
            high = bounds["max_value"]
            param = Parameter(kind='continuous', name=param, low=low, high=high)
            self.param_space.add(param)

        self.logger.debug('Built Parameter Space: %s', self.param_space)

        return self.param_space

    def build_planner(self):
        """
        Build Olympus.Planner.

        Args:
            param_space (Olympus.ParameterSpace)    Optimizer data
        """
        self.planner = Planner(param_space=self.param_space, **self.algorithm_props)

        return self.planner

    def register_result(self, request):
        """
        Add latest run to Olympus.compaign.observations and pass to Olympus.Planner.
        """

        parameters = []

        for batch in request[PARAMETERS]:

            param_set = []

            for param in batch.values():
                param_set.append(param["current_value"])
            
            parameters.append(param_set)

        results = list(data["result"].values())

        #FIXME Pass parameters and results in right format...currently looks buggy
        self.observations.add_observation(parameters, results)

    def query_next_experiment(self):
        """
        Ask planner for next point
        """
        point = self.planner.ask()
        return point.to_dict()


    def __call__(self, request):
        """
        Main call to handle request.
        """
        if self.planner is None:
            self.build_paramspace(request)
            self.build_planner()
            return {'planner': self.planner.to_dict()}

        if 'result' in request:
            self.register_result(request)

        next_experiment = self.query_next_experiment()
        # appending strategy for client backup
        # next_experiment.update(planner=self.planner.to_dict())
        return next_experiment
