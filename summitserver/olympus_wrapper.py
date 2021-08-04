"""
Module represents an optimization request handler.
"""
import logging
from typing import Union, Any
from olympus import ParameterSpace, Parameter
from olympus import Planner, Observations

#from .constants import ALGORITHMS_MAPPING


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
        self.planner = Planner(
            param_space=self.param_space,
            goal='maximize', **self.algorithm_props)

        return self.planner

    def register_result(self, request):
        """
        Add latest run to Olympus.compaign.observations and pass to Olympus.Planner.
        """
        if request[N_BATCHES] == -1:
            #FIXME
            # load all values
            pass
        elif request[N_BATCHES] == 1:
            parameters = []
            param_set = []
            for vals in request[PARAMETERS].values():
                param_set.append(vals[-1])
            parameters.append(param_set)           
            #TODO add results
        else:
            raise NotImplementedError("Parallel Optimization is not supported with Olympus.")

        # parameters = []
        # for i in range(self.batch_size):
        #     param_set = []
        #     for vals in request[PARAMETERS].values():
        #         param_set.append(vals[i])
        #     parameters.append(param_set)

        # Needs to be changed for multi-objectives
        #FIXME
        results = list(request[RESULT].values())[0]

        #FIXME Pass parameters and results in right format...currently looks buggy
        self.observations.add_observation(parameters, results)

    def query_next_experiment(self):
        """
        Ask planner for next point
        """
        # parallel not supported, always return n=1 points
        point = self.planner.ask()
        return {"batch 1":point.to_dict()}


    def __call__(self, request):
        """
        Main call to handle request.
        request: {"hash":"abc", "parameters":{}}

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

        #
        # {"batch 1": {"Add_1": 4.1, "Wait_2": 6.15},
        # "batch 2: {"Add_1": 2.5, "Wait_2": 1.5}"}
