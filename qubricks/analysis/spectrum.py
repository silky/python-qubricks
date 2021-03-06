import numpy as np
import warnings

def energy_spectrum(system, states, ranges, input=None, output=None, hamiltonian=None, components=[], params={}, hamiltonian_init=None, components_init=None, params_init=None, complete=False):
    '''
    This function returns a list of sequence which are the energy eigenvalues of the 
    states which map adiabatically to those provided in `states`. Consequently, the provided
    states should be eigenstates of the Hamiltonian (determined by `components_init` or 
    `hamiltonian_init`) when the parameters are set according to `params_init`. Where the initial
    conditions are not set, the states are assumed to be eigenstates of the Hamiltonian provided 
    for analysis (`hamiltonian` or `components`) in the corresponding parameter context `params`.
    
    :param system: A QuantumSystem instance.
    :type system: QuantumSystem
    :param states: A list of states (assumed to be eigenstates as noted above) for which we are
        interested in examining the eigen-spectrum.
    :type states: list of object
    :param ranges: A range specification for iteration (see `Parameters.range`).
    :type ranges: dict
    :param input: The basis of the specified states.
    :type input: str, Basis or None
    :param output: The basis in which to perform the calculations.
    :type output: str, Basis or None
    :param hamiltonian: The Hamiltonian for which a spectrum is desired.
    :type hamiltonian: Operator or None
    :param components: If `hamiltonian` is `None`, the components to use from the provided
        `QuantumSystem` (see `QuantumSystem.H`).
    :type components: list of str
    :param params: The parameter context in which to perform calculations.
    :type params: dict
    :param hamiltonian_init: The Hamiltonian for which provided states are eigenstates. If not
        provided, and `components_init` is also not provided, this defaults to the value of `hamiltonian`.
    :type hamiltonian_init: Operator
    :param components_init: The components to enable such that the provided states are eigenstates.
        If not provided, this defaults to the value of `components`. (see `QuantumSystem.H`)
    :type components: list of str
    :param params_init: The parameter context to be used such that the provided states are eigenstates
        of the initial Hamiltonian. If not provided, defaults to the value of `params`.
    :type params_init: dict
    :param complete: If `True`, then the eigen-spectrum of the remaining states not specifically requested
        are appended to the returned results.
    :type complete: bool
    
    .. warning:: Since this method uses the ordering of the eigenvalues to detect which eigenvalues
        belong to which eigenstates, this method does not work in cases when the adiabatic
        theorem is violated (i.e. when energy levels cross).
    '''

    if hamiltonian_init is None:
        if hamiltonian is None:
            hamiltonian_init = system.H(*(components_init if components_init is not None else components))
        else:
            hamiltonian_init = hamiltonian
    hamiltonian_init = hamiltonian_init.change_basis(system.basis(output), params=params)

    state_specs = states
    states = system.subspace(states, input=input, output=output, params=params)

    if type(ranges) is not dict:
        raise ValueError("Multi-dimensional ranges are not supported; and so ranges must be a dictionary.")

    # IDENTIFY WHICH STATES BELONG TO WHICH LABELS BY PROJECTING THEM ONTO EIGENSTATES
    if params_init is None:
        params_init = params
    evals,evecs = np.linalg.eig(hamiltonian_init(**params_init))
    evecs = evecs[:,np.argsort(evals)]
    evals = np.sort(evals)

    indices = np.argmax(np.array(states).dot(evecs),axis=1)
    if len(set(indices)) != len(indices):
        warnings.warn("Could not form bijective map between states and eigenvalues. Consider changing the initial conditions. Labelling may not work.")

    # Now iterate over the ranges provided, allocating state labels according
    # to the state which adiabatically maps to the current state. This assumes no
    # level crossings.
    if hamiltonian is None:
        hamiltonian = system.H(*components)
    hamiltonian = hamiltonian.change_basis(system.basis(output), params=params)

    # Generate values to iterate over
    f_ranges = params.copy() # merge ranges and params to ensure consistency
    f_ranges.update(ranges)
    rvals = system.p.range(*ranges.keys(),**f_ranges)
    if type(rvals) != dict:
        rvals = {ranges.keys()[0]: rvals}

    if not complete:
        results = np.zeros((len(states),len(rvals.values()[0])))
    else:
        results = np.zeros((system.dim,len(rvals.values()[0])))

    for i in xrange(len(rvals.values()[0])):
        vals = params.copy()
        for val in rvals:
            vals[val] = rvals[val][i]
        evals = sorted(np.linalg.eigvals(hamiltonian(**vals)))

        results[:len(indices),i] = [evals[indices[j]] for j in xrange(len(indices))]
        if complete:
            count = 0
            for k in xrange(system.dim):
                if k not in indices:
                    results[len(indices)+count,i] = evals[k]
                    count += 1

    return results
