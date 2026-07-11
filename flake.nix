{
  description = "Generate themes inspired by music cover art";

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

        build_pkgs = with pkgs; [
          gcc
          nodejs
          pnpm
          uv
        ];

        runtime_pkgs = with pkgs; [
          dbus
          fontconfig
          freetype
          glib
          libcap
          libglvnd
          libice
          libsm
          libx11
          libxcb
          libxcb-image
          libxcb-keysyms
          libxcb-render-util
          libxcb-wm
          libxext
          libxkbcommon
          openssl
          openxr-loader
          stdenv.cc.cc
          wayland
          xcb-util-cursor
          zlib
          SDL2
          SDL2_image
          SDL2_mixer
          SDL2_ttf
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
          taplo
        ];

        jukeboxPackage = pkgs.stdenv.mkDerivation {
          pname = "jukebox";
          version = "0.1.0";
          src = ./.;

          installPhase = ''
            mkdir -p $out/share/themes/

            cp -r output/* $out/share/themes/
          '';

          meta = {
            description = "Generate themes inspired by music cover art";
            homepage = "https://github.com/nooneknowspeter/jukebox";
            license = pkgs.lib.licenses.mit;
          };
        };
      in
      {
        devShells = {
          default = pkgs.mkShell {
            packages = [
            ]
            ++ build_pkgs
            ++ runtime_pkgs
            ++ dev_pkgs
            ++ fmt_pkgs;

            NIX_LD = pkgs.stdenv.cc.bintools.dynamicLinker;

            NIX_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath runtime_pkgs;

            buildInputs = runtime_pkgs;

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
      }
    );
}
