import numpy as np
import autograd.scipy as agsp
from bayes_lib.math.optimizers import GradientDescent
from .variational_distributions import *
import abc

class BlackBoxVariationalInference(object):

    __v_dist = None

    def __init__(self, model, variational_dist = MeanField, init = None):

        assert variational_dist.is_differentiable
        self.model = model
        self.v_dist = variational_dist(self.model.n_params, init = init)

    @property
    def v_dist(self):
        return self.__v_dist

    @v_dist.setter
    def v_dist(self, v_dist):
        self.__v_dist = v_dist

    def run(self, optimizer = GradientDescent(learning_rate = 1e-4)):

        def mc_elbo(v_pars, n_samples = 10):
            self.v_dist.variational_params = v_pars
            v_samples = self.v_dist.sample(n_samples)
            logq_model = self.v_dist.log_density(v_samples)

            elbo_est = 0
            for i in range(n_samples):
                logp_model = self.model.log_density_p(v_samples[i,:])
                elbo_est += logp_model - logq_model[i]
            return elbo_est/n_samples

        def mc_grad_elbo(v_pars, n_samples = 10):
            self.v_dist.variational_params = v_pars
            v_samples = self.v_dist.sample(n_samples)
            logq_model = self.v_dist.log_density(v_samples)
            
            grad_values = self.v_dist.grad_log_density(v_samples)
            for i in range(n_samples):
                logp_model = self.model.log_density_p(v_samples[i,:])
                grad_values[i,:] = grad_values[i,:] * (logp_model - logq_model[i])
            return np.mean(grad_values, axis = 0)

        #optimizer = GradientDescent(learning_rate = 1e-3)
        res = optimizer.run(lambda x: -mc_elbo(x), lambda x: -mc_grad_elbo(x), self.v_dist.variational_params, max_iters = 1000, convergence = 1e-3)
        self.v_dist.variational_params = res.position
        return res, self.v_dist