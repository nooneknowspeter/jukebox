{
  description = "themes inspired by music cover art";

  inputs = {
    flake-utils = {
      url = "github:numtide/flake-utils";
    };

    nixpkgs = {
      url = "github:nixos/nixpkgs/nixpkgs-unstable";
    };
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;

          config = {
            allowUnfree = true;
          };
        };

        runtime_pkgs = with pkgs; [
          uv
        ];

        dev_pkgs = with pkgs; [
          act
          direnv
          git
          just
        ];

        fmt_pkgs = with pkgs; [
          treefmt

          nixfmt
          prettier
          ruff
        ];
      in
      {
        devShells = {
          default = pkgs.mkShell {
            packages = [
            ]
            ++ runtime_pkgs
            ++ dev_pkgs
            ++ fmt_pkgs;
          };

          fmt = pkgs.mkShell {
            packages = with pkgs; [ just ] ++ fmt_pkgs;
          };
        };
      }
    );
}
