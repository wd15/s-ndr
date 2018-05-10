import fipy
from toolz.curried import memoize, do, curry, valmap, first, pipe
from toolz_ import update, iterate_, rcompose, save


def get_params():
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
        faraday=96485.332,
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
        vel=10.0e+6,
        output=True,
    )


def get_b(var):
    return float(var[0])


@curry
def theta_eqn(params, sup, theta, **kwargs):

    def expression1():
        return theta["old"] + params["dt"] * params["k_plus"] * get_b(sup)

    def expression2():
        return params["k_plus"] * get_b(sup) + params["k_minus"] * params["vel"]

    @memoize
    def new_value():
        return expression1() / (1 + params["dt"] * expression2())

    return (dict(new=new_value(), old=theta["old"]), abs(new_value() - theta["new"]))


get_mask = rcompose(
    lambda x: fipy.CellVariable(mesh=x),
    do(lambda x: x.setValue(1, where=x.mesh.x < x.mesh.dx)),
)


@save
def get_eqn(params, mesh):
    flux = fipy.CellVariable(mesh, value=0.)
    eqn = fipy.TransientTerm() == fipy.DiffusionTerm(
        params["diff_sup"]
    ) + fipy.ImplicitSourceTerm(
        flux * get_mask(mesh) / mesh.dx
    )

    def func(theta):
        flux.setValue(-params["gamma"] * params["k_plus"] * (1 - theta["new"]))
        return eqn

    return func


@curry
def sup_eqn(params, sup, theta, **kwargs):
    res = get_eqn(params, sup.mesh)(theta).sweep(sup, dt=params["dt"])
    return (sup, res)


@curry
def output_sweep(params, values):
    keys = ("sweeps", "sup", "theta")
    space = " " * 3
    lj = 20
    if values["sweeps"][0] == 1:
        print(space.join(map(lambda x: x.ljust(lj), keys)))
        print(space.join(["-" * (lj)] * len(keys)))

    def sci(v):
        return "{:.3E}".format(v)

    def get_res(key):
        if key == "sweeps":
            return str(values[key][0]).ljust(lj // 2)

        else:
            return sci(values[key][1]).ljust(lj // 2 + 1)

    def get_val(key):
        if key == "sweeps":
            return " ".rjust(lj // 2)

        elif key == "sup":
            return sci(float(values[key][0][0]))

        elif key == "theta":
            return sci(float(values[key][0]["new"]))

    print(space.join(map(lambda k: get_res(k) + get_val(k), keys)))


@curry
def output_step(params, values):
    print()
    print("step:", values["steps"])
    print()


def sweep_func(params):
    return rcompose(
        update(
            dict(
                sup=sup_eqn(params),
                theta=theta_eqn(params),
                steps=lambda **x: (x["steps"], None),
                sweeps=lambda **x: (x["sweeps"] + 1, None)
            )
        ),
        do(lambda x: output_sweep(params) if params["output"] else None),
        valmap(first)
    )


@curry
def step_func(params):
    return rcompose(
        do(lambda x: output_step(params) if params["output"] else None),
        update(
            dict(
                sup=lambda **x: do(lambda x: x.updateOld())(x["sup"]),
                theta=lambda **x: dict(new=x["theta"]["new"], old=x["theta"]["new"]),
                steps=lambda **x: x["steps"] + 1,
                sweeps=lambda **x: 0
            )
        ),
        iterate_(sweep_func(params), params["max_sweeps"])
    )


@curry
def run_values(params, values):
    return iterate_(step_func(params), params["max_steps"], values)


def get_mesh(params):
    return fipy.Grid1D(nx=params["nx"], dx=params["delta"] / params["nx"])


def get_sup_var(params):
    return pipe(
        params,
        get_mesh,
        lambda x: fipy.CellVariable(x, value=params["sup_ini"], hasOld=True),
        do(lambda x: x.constrain(params["sup_inf"], where=x.mesh.facesRight)),
    )


def run(params):
    return iterate_(
        step_func(params),
        params["max_steps"],
        dict(
            theta=dict(new=params["theta_ini"], old=params["theta_ini"]),
            sup=get_sup_var(params),
            sweeps=0,
            steps=0,
        ),
    )


if __name__ == "__main__":
    out = run(
        dict(
            get_params(),
            diff_sup=1.0,
            sup_inf=1.0,
            delta=1.0,
            k_plus=1.0,
            k_minus=1.0,
            vel=0.5,
            gamma=1.0,
            dt=1e+10,
            nx=1000,
            max_steps=1,
            max_sweeps=15,
        )
    )

    print(out)
