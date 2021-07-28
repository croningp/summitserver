"""
Module represents an optimization request handler.
"""

from olympus import ParameterSpace
from olympus import Planner, Observations

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

        self.param_space = ParameterSpace()

        self.observations = Observations()

        self.planner = None

        self.suggestion = None


    def build_paramspace(self, data):
        """
        Build Olympus.ParameterSpace.

        Args:
            data (Nested Dict)    Optimizer data
        """

        for param, bounds in data["parameters"].items():

            low = bounds["min_value"]
            high = bounds["max_value"]
            param = Parameter(kind='continuous', name=param, low=low, high=high)
            self.param_space.add(param)

        return self.param_space

    def build_planner(self):
        """
        Build Olympus.Planner.

        Args:
            param_space (Olympus.ParameterSpace)    Optimizer data
        """
        self.planner = Planner(param_space=self.param_space, **self.algorithm_props)

        return self.planner

    def register_result(self, data):
        """
        Add latest run to Olympus.compaign.observations and pass to Olympus.Planner.
        """

        parameters = []

        for param in data["parameters"].values():
            parameters.append(param["current_value"])

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
        next_experiment.update(planner=self.planner.to_dict())
        return next_experiment