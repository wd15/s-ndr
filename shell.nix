let
  inherit (import <nixpkgs> {}) fetchFromGitHub;
  download = fetchFromGitHub {
    owner = "wd15";
    repo = "nixes";
    rev = "fa3edd44073ea3bd5be9f0ad5b526d75fd1e013b";
    sha256 = "1m4dia78qp8w5n3rvzzfri3cbkbjamn17qib1gqfm179vyav5an3";
  };
  pkgs = nixpkgs.pkgs;
  nixpkgs = import "${download}/fipy-py3/nixpkgs_version.nix";
  fipy = import "${download}/fipy-py3/fipy.nix" { inherit nixpkgs; };
  skfmm = import "${download}/fipy-py3/skfmm.nix" { inherit nixpkgs; };
  nbval = import "${download}/fipy-py3/nbval.nix" { inherit nixpkgs; };
  pytest-cov = import "${download}/fipy-py3/pytest-cov.nix" { inherit nixpkgs; };
in
  nixpkgs.stdenv.mkDerivation rec {
    name = "s-ndr";
    env = nixpkgs.buildEnv { name=name; paths=buildInputs; };
    buildInputs = [
      nixpkgs.python36Packages.numpy
      nixpkgs.python36Packages.scipy
      nixpkgs.python36Packages.jupyter
      nixpkgs.python36Packages.toolz
      nixpkgs.python36Packages.pytest
      nixpkgs.python36Packages.pylint
      nixpkgs.python36Packages.ipdb
      nixpkgs.python36Packages.pip
      nixpkgs.python36Packages.matplotlib
      nixpkgs.python36Packages.flake8
      nixpkgs.python36Packages.ipywidgets
      nixpkgs.python36Packages.tkinter
      fipy
      skfmm
      nbval
      pytest-cov
    ];
    shellHook = ''
      jupyter nbextension install --py widgetsnbextension --user
      jupyter nbextension enable widgetsnbextension --user --py
    '';

  }
