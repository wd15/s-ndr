"""Main function for running S-NDR equations

See the notebooks for more details on usage.
"""

# pylint: disable=no-value-for-parameter

import numpy
import fipy
from toolz.curried import memoize, do, curry, valmap, first, pipe
from toolz_ import update, iterate_, rcompose, save


def get_params():
    """The base parameters

    Returns:
      a dictionary of parameter values
    """
    return dict(
        diff_sup=9.2e-11,
        diff_cu=2.65e-10,
        cu_inf=240.0,
        sup_inf=0.01,
        delta=1e-6,
        gamma=2.5e-7,
        k_plus=2300.0,
        k_minus=3.79e-6,
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


def calc_j0(params, eta):
    """Calculate j0

    Args:
      params: the parameter dictionary
      eta: the potential

    Returns:
      the value of j0
    """
    return params["j0"] * eta_func(params, eta)


def calc_j1(params, eta):
    """Calculate j1

    Args:
      params: the parameter dictionary
      eta: the potential

    Returns:
      the value of j1
    """
    return params["j1"] * eta_func(params, eta)


@curry
def theta_eqn(params, sup, theta, eta, **kwargs):  # pylint: disable=unused-argument
    """Update the suppressor interface value

    Args:
      params: the parameter dictionary
      sup: the buld suppressor variable
      theta: the interface suppressor dictionary
      kwargs: other, unused variables

    Returns:
      the updated theta value dictionary and the residual
    """

    def left(var):
        """Get left value of variable
        """
        return float(var[0])

    def expression1():
        """Evaluation expression for theta equation
        """

        return theta["old"] + params["dt"] * (
            params["k_plus"]
            * left(sup)
            + theta["new"]
            ** 2
            * params["k_minus"]
            * (calc_j0(params, eta) - calc_j1(params, eta))
        )

    def expression2():
        """Evaluation expression for theta equation
        """
        return params["k_plus"] * left(sup) + params["k_minus"] * calc_j0(params, eta)

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


@save
def get_eqn(params, mesh):
    """Generate the buld suppressor equation.

    This equation is cached and is only run once.

    Args:
      params: the parameter dictionary
      mesh: the mesh

    Returns:
      a function that updates the equation
    """
    flux = fipy.CellVariable(mesh, value=0.)
    eqn = fipy.TransientTerm() == fipy.DiffusionTerm(
        params["diff_sup"]
    ) + fipy.ImplicitSourceTerm(
        flux * GET_MASK(mesh) / mesh.dx
    )

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


@curry
def sup_eqn(params, sup, theta, **kwargs):  # pylint: disable=unused-argument
    """Update the bulk suppressor variable

    Args:
      params: the parameter dictionary
      sup: the buld suppressor variable
      theta: the interface suppressor dictionary
      kwargs: other unused variables

    Returns:
      the update buld suppressor and the residual
    """
    res = get_eqn(params, sup.mesh)(theta).sweep(sup, dt=params["dt"])
    return (sup, res)


@curry
def output_sweep(values):
    """Output sweep data

    Args:
      params: the parameter dictionary
      values: the variable values dictionary
    """
    keys = ("sweeps", "sup", "theta")
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

        elif key == "sup":
            return sci(float(values[key][0][0]))

        elif key == "theta":
            return sci(float(values[key][0]["new"]))

        return ""

    print(space.join(map(lambda k: get_res(k) + get_val(k), keys)))


@curry
def output_step(values):
    """Output the step data

    Args:
      params: the parameter dictionary
      values: the value dictionary
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
        update(
            dict(
                sup=sup_eqn(params),
                theta=theta_eqn(params),
                steps=lambda **x: (x["steps"], None),
                sweeps=lambda **x: (x["sweeps"] + 1, None),
                eta=lambda **x: (calc_eta(params, x["steps"]), None)
            )
        ),
        do(lambda x: output_sweep if params["output"] else None),
        valmap(first)
    )


@curry
def step_func(params):
    """Generate the steping function

    Args:
      params: the parameter dictionary

    Returns:
      a function to do a time step
    """
    return rcompose(
        do(lambda x: output_step if params["output"] else None),
        update(
            dict(
                sup=lambda **x: do(lambda x: x.updateOld())(x["sup"]),
                theta=lambda **x: dict(new=x["theta"]["new"], old=x["theta"]["new"]),
                steps=lambda **x: x["steps"] + 1,
                sweeps=lambda **x: 0,
                eta=lambda **x: x["eta"]
            )
        ),
        iterate_(sweep_func(params), params["max_sweeps"])
    )


def get_mesh(params):
    """Make the mesh

    Args:
      params: the parameter dictioniary

    Returns:
      the mesh
    """
    return fipy.Grid1D(nx=params["nx"], dx=params["delta"] / params["nx"])


def get_sup_var(params):
    """Make the bulk suppressor variable with constraint

    Args:
      params: the parameter dictionary

    Returns:
      the bulk suppressor variable
    """
    return pipe(
        params,
        get_mesh,
        lambda x: fipy.CellVariable(x, value=params["sup_ini"], hasOld=True),
        do(lambda x: x.constrain(params["sup_inf"], where=x.mesh.facesRight)),
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
            sup=get_sup_var(params),
            sweeps=0,
            steps=0,
            eta=calc_eta(params, 0),
        ),
    )
