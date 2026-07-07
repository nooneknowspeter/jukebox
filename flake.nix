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
          htmlq
          jq
          just
          opencode
        ];

        fmt_pkgs = with pkgs; [
          treefmt

          isort
          nixfmt
          prettier
          ruff
        ];

        jukeboxPackage = pkgs.python3Packages.buildPythonPackage {
          pname = "jukebox";
          version = "0.2.0";
          src = ./.;
          pyproject = true;

          build-system = with pkgs.python3Packages; [
            setuptools
          ];

          dependencies = with pkgs.python3Packages; [
            beautifulsoup4
            jinja2
            pillow
            pyyaml
            regex
            requests
          ];
        };
      in
      {
        devShells = {
          default = pkgs.mkShell {
            packages = [
            ]
            ++ runtime_pkgs
            ++ dev_pkgs
            ++ fmt_pkgs;

            shellHook = ''
              if [ ! -d .venv ]; then
                  uv venv
              fi

              source .venv/bin/activate

              uv sync
            '';
          };

          fmt = pkgs.mkShell {
            packages = with pkgs; [ just ] ++ fmt_pkgs;
          };
        };

        packages = {
          default = jukeboxPackage;
          jukebox = jukeboxPackage;
        };

        apps.default = {
          type = "app";
          program = "${jukeboxPackage}/bin/jukebox";
        };
      }
    );
}
