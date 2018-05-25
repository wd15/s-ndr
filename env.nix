{ with_latex }:
let
  inherit (import <nixpkgs> {}) fetchFromGitHub;
  download = fetchFromGitHub {
    owner = "wd15";
    repo = "nixes";
    rev = "fa3edd44073ea3bd5be9f0ad5b526d75fd1e013b";
    sha256 = "1m4dia78qp8w5n3rvzzfri3cbkbjamn17qib1gqfm179vyav5an3";
  };
  pypkgs = nixpkgs.python36Packages;
  nixpkgs = import "${download}/fipy-py3/nixpkgs_version.nix";
  fipy = import "${download}/fipy-py3/fipy.nix" { inherit nixpkgs; };
  skfmm = import "${download}/fipy-py3/skfmm.nix" { inherit nixpkgs; };
  nbval = import "${download}/fipy-py3/nbval.nix" { inherit nixpkgs; };
  pytest-cov = import "${download}/fipy-py3/pytest-cov.nix" { inherit nixpkgs; };
  texlive = nixpkgs.pkgs.texlive;
  latex = if with_latex then
    (texlive.combine { inherit (texlive) scheme-medium collection-latexextra; })
  else
    null;
in
  nixpkgs.stdenv.mkDerivation rec {
    name = "s-ndr";
    env = nixpkgs.buildEnv { name=name; paths=buildInputs; };
    buildInputs = [
      pypkgs.numpy
      pypkgs.scipy
      pypkgs.jupyter
      pypkgs.toolz
      pypkgs.pytest
      pypkgs.pylint
      pypkgs.ipdb
      pypkgs.pip
      pypkgs.matplotlib
      pypkgs.flake8
      pypkgs.ipywidgets
      nixpkgs.python36Packages.tkinter
      fipy
      skfmm
      nbval
      pytest-cov
      latex
    ];
    shellHook = ''
      jupyter nbextension install --py widgetsnbextension --user
      jupyter nbextension enable widgetsnbextension --user --py
    '';
  }
