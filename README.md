

# S-NDR: Solving the S-NDR Equations in 1D

<p align="center">
<a href="https://travis-ci.org/wd15/s-ndr" target="_blank">
<img src="https://api.travis-ci.org/wd15/s-ndr.svg"
alt="Travis CI">
</a>
</p>


This repository solves the 1D S-NDR equations for electrochemistry. The equations are outlined in [index.ipynb](./index.ipynb). They consist of two diffusion field equations and an equation that only evolves at the boundary of the domain. The equations are solved using [FiPy](https://www.ctcms.nist.gov/fipy/)

# Installation and Usage

Either use Nix or Docker

## Nix

Follow these [Nix
notes](https://github.com/wd15/nixes/blob/master/NIX-NOTES.md) for
installing Nix.

After installing Nix and cloning this repository, run

    $ nix-shell

to get an environment to run the notebook examples

## Docker

See [the Docker instructions](./DOCKER.md).

# Testing

Run all the tests with

    $ nix-shell --command "py.test"

# License

The license is the [MIT license](./LICENSE).
