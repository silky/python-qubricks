import numpy as np

from ..stateoperator import StateOperator
from ..utility import dot


class DummyStateOperator(StateOperator):
    '''
    An StateOperator instance that does nothing to the state, but which
    forces the integrator to work as if it were necessary to evolve ensemble
    states.
    '''

    def __call__(self, state, t=0, params={}):
        return state

    def init(self, **kwargs):
        pass

    def transform(self, transform_op):
        return self

    def restrict(self, *indicies):
        return self

    def connected(self, *indicies, **params):
        return set(indicies)

    def collapse(self, *wrt, **params):
        return self

    @property
    def for_state(self):
        return False

    @property
    def for_ensemble(self):
        return True


class SchrodingerStateOperator(StateOperator):
    '''
    A StateOperator instance that effects Schroedinger evolution of the
    (quantum) state.
    '''

    def init(self, H):
        self.H = self.Operator(H)

    def __call__(self, state, t=0, params={}):
        pams = {'t':t}
        pams.update(params)
        if len(state.shape) > 1:
            H = self.H(t=t, **params)
            return 1j / self.p.c_hbar * (np.dot(state, H) - np.dot(H, state))
        return -1j / self.p.c_hbar * self.H.apply(state, params=pams, left=True, symbolic=False)  # This may provide a speedup over np.dot(H, state)

    def transform(self, transform_op):
        return SchrodingerStateOperator(self.p, H=transform_op(self.H))

    def restrict(self, *indicies):
        return SchrodingerStateOperator(self.p, H=self.H.restrict(*indicies))

    def connected(self, *indicies, **params):
        return self.H.connected(*indicies, **params)

    def collapse(self, *wrt, **params):
        return SchrodingerStateOperator(self.p, H=self.H.collapse(*wrt, **params), basis=self.basis)

    @property
    def for_state(self):
        return True

    @property
    def for_ensemble(self):
        return True


class LindbladStateOperator(StateOperator):
    '''
    A StateOperator instance that effects a single-termed Lindblad master equation. This will cause decay in a simple
    two level system proportional to: exp(-8*coefficient*t)
    '''

    def init(self, coefficient, operator):
        self.coefficient = coefficient
        self.operator = self.Operator(operator)

    def __call__(self, state, t=0, params={}):
        O = self.operator(t=t, **params)
        Od = O.transpose().conjugate()

        return self.p(self.coefficient, t=t, **params) / self.p.c_hbar ** 2 * (dot(O, state, Od) - 0.5 * (dot(Od, O, state) + dot(state, Od, O)))

    def transform(self, transform_op):
        return LindbladStateOperator(self.p, coefficient=self.coefficient, operator=transform_op(self.operator))

    def restrict(self, *indicies):
        return LindbladStateOperator(self.p, coefficient=self.coefficient, operator=self.operator.restrict(*indicies))
        # No basis reported since that does not make sense when restricted

    def connected(self, *indicies, **params):
        return self.operator.connected(*indicies, **params)

    def collapse(self, *wrt, **params):
        return LindbladStateOperator(self.p, coefficient=self.coefficient, operator=self.operator.collapse(*wrt, **params), basis=self.basis)

    @property
    def for_state(self):
        return False

    @property
    def for_ensemble(self):
        return True
