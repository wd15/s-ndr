let
  inherit (import <nixpkgs> {}) fetchFromGitHub;
  download = fetchFromGitHub {
    owner = "wd15";
    repo = "nixes";
    rev = "5b675f0b26450daf6762e9f6682463eebb548258";
    sha256 = "0086bd6cdp0xlr8nbfs6ypmlg0h2xb7rlvhqciv75r86k9jc55i4";
  };
  nixpkgs = import "${download}/fipy-py3/nixpkgs_version.nix";
  fipy = import "${download}/fipy-py3/fipy.nix" { inherit nixpkgs; };
  gmsh = import "${download}/fipy-py3/gmsh.nix" { inherit nixpkgs; };
  skfmm = import "${download}/fipy-py3/skfmm.nix" { inherit nixpkgs; };
in
  nixpkgs.stdenv.mkDerivation rec {
    name = "fipy-py3-env";
    env = nixpkgs.buildEnv { name=name; paths=buildInputs; };
    buildInputs = [
      nixpkgs.python36Packages.numpy
      nixpkgs.python36Packages.scipy
      nixpkgs.python36Packages.jupyter
      nixpkgs.python36Packages.toolz
      nixpkgs.python36Packages.pytest
      nixpkgs.python36Packages.ipdb
      fipy
      gmsh
      skfmm

    ];
  }
