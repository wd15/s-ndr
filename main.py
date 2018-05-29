"""Main function for running S-NDR equations

See the notebooks for more details on usage.
"""

# pylint: disable=no-value-for-parameter

import numpy
import fipy
from toolz.curried import do, curry, valmap, first, pipe
from toolz.curried import memoize, identity, get, itemmap
from toolz_ import update_dict, iterate_, rcompose, cache


def get_params():
    """The base parameters

    Returns:
      a dictionary of parameter values
    """
    return dict(
        diff_sup=9.2e-11,
        diff_cupric=2.65e-10,
        cupric_inf=240.0,
        sup_inf=0.01,
        delta=1e-6,
        gamma=2.5e-7,
        k_plus=2300.0,
        k_minus=3.79e+7,
        j0=20.0,
        j1=1e-3,
        alpha=0.4,
        n=2,
        omega=7.2e-6,
        F=96485.332,
        v0=0,
        vs=-0.325,
        vm=0.01,
        tf=65.0,
        max_sweeps=4,
        max_steps=400,
        theta_ini=0.0,
        sup_ini=0.0,
        cupric_ini=0.0,
        nx=100,
        dt=1e-3,
        output=True,
        T=270.0,
        R=8.314,
    )


def eta_func(params, eta):
    """Calculate the forward / backward jump

    Args:
      params: the parameter dictionary
      eta: the potential

    Returns:
      single value for jump

    >>> assert eta_func(get_params(), 0) == 0
    """
    return pipe(
        eta * params["n"] * params["F"] / params["R"] / params["T"],
        lambda x: numpy.exp(params["alpha"] * x) - numpy.exp(-(1 - params["alpha"]) * x)
    )


def left(var):
    """Get left value of variable
    """
    return float(var[0])


def calc_j0(params, eta, cupric):
    """Calculate j0

    Args:
      params: the parameter dictionary
      eta: the potential
      cu: the cupric variable

    Returns:
      the value of j0
    """
    return params["j0"] * eta_func(params, eta) * left(cupric) / params["cupric_inf"]


def calc_j1(params, eta, cupric):
    """Calculate j1

    Args:
      params: the parameter dictionary
      eta: the potential
      cupric: the cupric variable

    Returns:
      the value of j1
    """
    return params["j1"] * eta_func(params, eta) * left(cupric) / params["cupric_inf"]


# pylint: disable=unused-argument


@curry
def theta_eqn(params, sup, theta, eta, cupric, **kwargs):
    """Update the suppressor interface value

    Args:
      params: the parameter dictionary
      sup: the buld suppressor variable
      theta: the interface suppressor dictionary
      cupric: the cupric variable
      kwargs: other, unused variables

    Returns:
      the updated theta value dictionary and the residual
    """

    def expression1():
        """Evaluation expression for theta equation
        """

        return theta["old"] + params["dt"] * (
            params["k_plus"]
            * left(sup)
            + theta["new"]
            ** 2
            * params["k_minus"]
            * calc_j0(params, eta, cupric)
        )

    def expression2():
        """Evaluation expression for theta equation
        """
        return params["k_plus"] * left(sup) + params["k_minus"] * (
            calc_j0(params, eta, cupric) + theta["new"] * calc_j1(params, eta, cupric)
        )

    @memoize
    def new_value():
        """Calculate and cache the new value
        """
        return expression1() / (1 + params["dt"] * expression2())

    return (dict(new=new_value(), old=theta["old"]), abs(new_value() - theta["new"]))


GET_MASK = rcompose(
    lambda x: fipy.CellVariable(mesh=x),
    do(lambda x: x.setValue(1, where=x.mesh.x < x.mesh.dx)),
)


def get_eqn(mesh, diff):
    """Generate a generic 1D diffusion equation with flux from the left

     Args:
      mesh: the mesh
      diff: the diffusion coefficient

    Returns:
      a tuple of the flux and the equation
    """
    flux = fipy.CellVariable(mesh, value=0.)
    eqn = fipy.TransientTerm() == fipy.DiffusionTerm(diff) + fipy.ImplicitSourceTerm(
        flux * GET_MASK(mesh) / mesh.dx
    )
    return (flux, eqn)


@cache
def get_cupric_eqn(params, mesh):
    """Generate the cupric equation.

    This equation is cached and is only run once.

    Args:
      params: the parameter dictionary
      mesh: the mesh

    Returns:
      a function that updates the equation
    """
    flux, eqn = get_eqn(mesh, params["diff_cupric"])

    def func(eta, theta):
        """Function that actually updates the equaton at each sweep.

        Args:
           eta: the potential
           theta: the new value of theta

        Returns:
           the updated equation
        """
        flux.setValue(
            -eta_func(params, eta)
            / params["omega"]
            / params["cupric_inf"]
            * (params["j0"] * (1 - theta["new"]) + params["j1"] * theta["new"])
        )
        return eqn

    return func


# pylint: disable=unused-argument, too-many-arguments


@curry
def cupric_eqn(params, cupric, eta, theta, sweeps, steps, **kwargs):
    """Update the bulk suppressor variable

    Args:
      params: the parameter dictionary
      eta: the potential value
      theta: the interface suppressor dictionary
      kwargs: other unused variables

    Returns:
      the updated cupric value and the residual
    """
    update = False
    if sweeps == 0 and steps == 0:
        update = True
    # pylint: disable=unexpected-keyword-arg
    res = get_cupric_eqn(params, cupric.mesh, update=update)(eta, theta).sweep(
        cupric, dt=params["dt"]
    )
    return (cupric, res)


@cache
def get_sup_eqn(params, mesh):
    """Generate the buld suppressor equation.

    This equation is cached and is only run once.

    Args:
      params: the parameter dictionary
      mesh: the mesh

    Returns:
      a function that updates the equation
    """
    flux, eqn = get_eqn(mesh, params["diff_sup"])

    def func(theta):
        """Function that actually updates the equaton at each sweep.

        Args:
           theta: the new value of theta

        Returns:
           the updated equation
        """
        flux.setValue(-params["gamma"] * params["k_plus"] * (1 - theta["new"]))
        return eqn

    return func


# pylint: disable=unused-argument


@curry
def sup_eqn(params, sup, theta, sweeps, steps, **kwargs):
    """Update the bulk suppressor variable

    Args:
      params: the parameter dictionary
      sup: the buld suppressor variable
      theta: the interface suppressor dictionary
      kwargs: other unused variables

    Returns:
      the update buld suppressor and the residual
    """
    update = False
    if sweeps == 0 and steps == 0:
        update = True
    # pylint: disable=unexpected-keyword-arg
    res = get_sup_eqn(params, sup.mesh, update=update)(theta).sweep(
        sup, dt=params["dt"]
    )
    return (sup, res)


@curry
def output_sweep(values):
    """Output sweep data

    Args:
      params: the parameter dictionary
      values: the variable values dictionary

    >>> output_sweep(
    ...     dict(
    ...         sweeps=(1,),
    ...         sup=([1e-3], 1e-2),
    ...         theta=(dict(new=0.1, old=0.01), 1e-4),
    ...         eta=(1.0, 0.0)
    ...     )
    ... ) # doctest: +NORMALIZE_WHITESPACE
    sweeps                 sup                    theta                  eta
    --------------------   --------------------   --------------------   --------------------
    1                      1.000E-02  1.000E-03   1.000E-04  1.000E-01   0.000E+00  1.000E+00

    """  # noqa: E501
    keys = list(filter(lambda x: x != "steps", values.keys()))
    space = " " * 3
    ljustify = 20
    if values["sweeps"][0] == 1:
        print(space.join(map(lambda x: x.ljust(ljustify), keys)))
        print(space.join(["-" * (ljustify)] * len(keys)))

    def sci(value):
        """Format a float

        Args:
          value: the value to format

        Returns:
          formatted string
        """
        return "{:.3E}".format(value)

    def get_res(key):
        """Get the formatted residual

        Args:
          key: the key for the value

        Returns:
          the formatted residual
        """
        if key == "sweeps":
            return str(values[key][0]).ljust(ljustify // 2)

        return sci(values[key][1]).ljust(ljustify // 2 + 1)

    def get_val(key):
        """Get the formatted value

        Args:
          key: the key for the value

        Returns:
          the formatted value
        """
        if key == "sweeps":
            return " ".rjust(ljustify // 2)

        elif key == "theta":
            return sci(float(values[key][0]["new"]))

        elif key == "eta":
            return sci(float(values[key][0]))

        return sci(float(values[key][0][0]))

    print(space.join(map(lambda k: get_res(k) + get_val(k), keys)))


@curry
def output_step(values):
    """Output the step data

    Args:
      params: the parameter dictionary
      values: the value dictionary

    >>> output_step(dict(steps=1))
    <BLANKLINE>
    step: 1
    <BLANKLINE>
    """
    print()
    print("step:", values["steps"])
    print()


@curry
def calc_eta(params, steps, **kwargs):  # pylint: disable=unused-argument
    """Calculate the potential

    Args:
      params: the parameter dictionary
      steps: the current number of time steps

    Returns:
      the potential value

    >>> assert calc_eta(dict(dt=0.1, tf=1., vm=0.5, v0=0.), 4) == 0.2
    >>> assert calc_eta(dict(dt=0.1, tf=1., vm=0.5, v0=1.), 11) == 1.
    >>> assert calc_eta(dict(dt=0.1, tf=1., vm=0.5, v0=1.), 9) == 1.05

    """
    current = steps * params["dt"]
    if current < params["tf"] / 2:
        return params["v0"] + params["vm"] * current

    elif current < params["tf"]:
        return params["v0"] + params["vm"] * (params["tf"] - current)

    return params["v0"]


def sweep_func(params):
    """Do a sweep and update the variables

    Args:
      params: the parameter dictionary

    Returns:
      a function that modifies value dictionary
    """
    return rcompose(
        update_dict(
            dict(
                sup=sup_eqn(params),
                cupric=cupric_eqn(params),
                theta=theta_eqn(params),
                steps=lambda **x: (x["steps"], 0.0),
                sweeps=lambda **x: (x["sweeps"] + 1, 0.0),
                eta=lambda **x: (calc_eta(params, x["steps"]), 0.0),
                data=lambda **x: (x["data"], 0.0)
            )
        ),
        do(lambda x: output_sweep(x) if params["output"] else None),
        valmap(first)
    )


def update_data(data, **kwargs):
    """Update the temporal data dictionary

    Args:
      data: the temporal data dictionary

    Returns:
      the updated temporal data dictionary

    >>> mesh = fipy.Grid1D(nx=10)
    >>> out = update_data(
    ...     cupric=fipy.CellVariable(mesh=mesh, value=1.),
    ...     sup=fipy.CellVariable(mesh=mesh, value=2.),
    ...     theta=dict(new=3.),
    ...     eta=4.,
    ...     data=dict(cupric=[], sup=[], theta=[], eta=[])
    ... )
    >>> assert out == dict(cupric=[1.0], sup=[2.0], theta=[3.0], eta=[4.0])
    """

    def val(key, value):
        """Append the current temporal value to the list of previous values.
        """
        return value + [
            dict(sup=left, cupric=left, theta=get("new"), eta=identity)[key](
                kwargs[key]
            )
        ]

    return itemmap(lambda kv: (kv[0], val(kv[0], kv[1])), data)


@curry
def step_func(params):
    """Generate the steping function

    Args:
      params: the parameter dictionary

    Returns:
      a function to do a time step
    """
    return rcompose(
        do(lambda x: output_step(x) if params["output"] else None),
        update_dict(
            dict(
                sup=lambda **x: do(lambda x: x.updateOld())(x["sup"]),
                cupric=lambda **x: do(lambda x: x.updateOld())(x["cupric"]),
                theta=lambda **x: dict(new=x["theta"]["new"], old=x["theta"]["new"]),
                steps=lambda **x: x["steps"] + 1,
                sweeps=lambda **x: 0,
                eta=lambda **x: x["eta"],
                data=update_data
            )
        ),
        iterate_(sweep_func(params), params["max_sweeps"])
    )


@memoize
def get_mesh(ncells, delta):
    """Make the mesh

    Args:
      ncells: number of cells
      delta: the domain size

    Returns:
      the mesh
    """
    return fipy.Grid1D(nx=ncells, dx=delta / ncells)


def get_var(params, ini, inf):
    """Make a variable with constraint

    Args:
      params: the parameter dictionary
      ini: initial value
      inf: far field value

    Returns:
      the variable
    """
    return pipe(
        params,
        lambda x: get_mesh(x["nx"], x["delta"]),
        lambda x: fipy.CellVariable(x, value=ini, hasOld=True),
        do(lambda x: x.constrain(inf, where=x.mesh.facesRight)),
    )


def run(params):
    """Run the entire simulation

    Args:
      params: the parameter dictionary

    Returns:
      the value dictionary
    """
    return iterate_(
        step_func(params),
        params["max_steps"],
        dict(
            theta=dict(new=params["theta_ini"], old=params["theta_ini"]),
            sup=get_var(params, params["sup_ini"], params["sup_inf"]),
            cupric=get_var(params, params["cupric_ini"], params["cupric_inf"]),
            sweeps=0,
            steps=-1,
            eta=calc_eta(params, 0),
            data=dict(cupric=[], sup=[], theta=[], eta=[]),
        ),
    )
