# Sourced by non-interactive bash via BASH_ENV.
# Adds Nix to PATH without relying on nix.sh's once-guard.
if [ -d /nix/var/nix/profiles/default/bin ]; then
    case ":$PATH:" in
        *:/nix/var/nix/profiles/default/bin:*) ;;  # already on PATH
        *) export PATH="$HOME/.nix-profile/bin:/nix/var/nix/profiles/default/bin:$PATH" ;;
    esac
fi
