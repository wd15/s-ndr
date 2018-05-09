let
  inherit (import <nixpkgs> {}) fetchFromGitHub;
  download = fetchFromGitHub {
    owner = "wd15";
    repo = "nixes";
    rev = "5e58e59a945cd3ce3c39d88cc4618d4f426cd030";
    sha256 = "0gk9pd4a5n57dp9cm0x414j03ja5gim82pzzd7z6ww7wbqb03v9f";
  };
  pkgs = nixpkgs.pkgs;
  nixpkgs = import "${download}/fipy-py3/nixpkgs_version.nix";
  fipy = import "${download}/fipy-py3/fipy.nix" { inherit nixpkgs; };
  gmsh = import "${download}/fipy-py3/gmsh.nix" { inherit nixpkgs; };
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
      fipy
      gmsh
      skfmm
      nbval
    ];
  }
