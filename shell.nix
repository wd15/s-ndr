let
  inherit (import <nixpkgs> {}) fetchFromGitHub;
  download = fetchFromGitHub {
    owner = "wd15";
    repo = "nixes";
    rev = "5e58e59a945cd3ce3c39d88cc4618d4f426cd030";
    sha256 = "1s5hmgyxjfs5sgb13sx0rmnkgccmnkn6x64hhxrzjj1m71l5nkyw";
  };
  nixpkgs = import <nixpkgs> {};
  pkgs = nixpkgs.pkgs;
  # nixpkgs = import "${download}/fipy-py3/nixpkgs_version.nix";
  fipy = import "${download}/fipy-py3/fipy.nix" { inherit nixpkgs; };
  skfmm = import "${download}/fipy-py3/skfmm.nix" { inherit nixpkgs; };
  nbval = import "${download}/fipy-py3/nbval.nix" { inherit nixpkgs; };
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
      fipy
      skfmm
      nbval
    ];
    shellHook = ''
      jupyter nbextension install --py widgetsnbextension --user
      jupyter nbextension enable widgetsnbextension --user --py
    '';

  }
