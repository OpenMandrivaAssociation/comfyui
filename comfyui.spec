# ComfyUI: node-graph diffusion GUI. Models stay outside the package.

Name:		comfyui
Version:	0.37.1
Release:	1
Summary:	Modular diffusion model GUI, API and backend
License:	GPL-3.0
Group:		Sciences/Other
URL:		https://github.com/Comfy-Org/ComfyUI
Source0:	https://github.com/Comfy-Org/ComfyUI/archive/refs/tags/v%{version}/ComfyUI-%{version}.tar.gz
Source1:	extra_model_paths.yaml
BuildArch:	noarch

BuildRequires:	python
Requires:	python
Requires:	python%{pyver}dist(torch)
Requires:	python%{pyver}dist(torchvision)
Requires:	python%{pyver}dist(numpy)
Requires:	python%{pyver}dist(einops)
Requires:	python%{pyver}dist(transformers)
Requires:	python%{pyver}dist(tokenizers)
Requires:	python%{pyver}dist(sentencepiece)
Requires:	python%{pyver}dist(safetensors)
Requires:	python%{pyver}dist(aiohttp)
Requires:	python%{pyver}dist(yarl)
Requires:	python%{pyver}dist(pyyaml)
Requires:	python%{pyver}dist(pillow)
Requires:	python%{pyver}dist(scipy)
Requires:	python%{pyver}dist(tqdm)
Requires:	python%{pyver}dist(psutil)
Requires:	python%{pyver}dist(alembic)
Requires:	python%{pyver}dist(sqlalchemy)
Requires:	python%{pyver}dist(filelock)
Requires:	python%{pyver}dist(av)
Requires:	python%{pyver}dist(requests)
Requires:	python%{pyver}dist(simpleeval)
Requires:	python%{pyver}dist(blake3)
Requires:	python%{pyver}dist(torchsde)
Requires:	python%{pyver}dist(comfy-aimdo)
Requires:	python%{pyver}dist(comfy-kitchen)
Requires:	python%{pyver}dist(comfyui-frontend-package)
Recommends:	python%{pyver}dist(comfyui-embedded-docs)
Recommends:	python%{pyver}dist(spandrel)
Recommends:	python%{pyver}dist(pydantic)
Recommends:	python%{pyver}dist(pydantic-settings)
Recommends:	python%{pyver}dist(pyopengl)
Suggests:	python%{pyver}dist(torchaudio)
Suggests:	python%{pyver}dist(kornia)

%description
ComfyUI is a node-based interface for running diffusion models
(Qwen-Image, Flux, SDXL, …). The RPM ships the application only;
checkpoints go in /srv/ai or /media/space/ai (see
%{_sysconfdir}/comfyui/extra_model_paths.yaml).

User data (output, input, custom_nodes, temp) is under
$XDG_DATA_HOME/comfyui (default ~/.local/share/comfyui).

  comfyui
  # then open http://127.0.0.1:8188/

Qwen-Image needs a diffusion GGUF/safetensors, the Qwen Image VAE
and Qwen2.5-VL 7B as the text encoder. Stop llama.service first if
the GPU is already full.

%prep
%autosetup -p1 -n ComfyUI-%{version}

%build

%install
install -d %{buildroot}%{_datadir}/comfyui
# Application code. Empty model/output placeholders stay in the
# per-user --base-directory, not under /usr.
for d in alembic_db api_server app blueprints comfy comfy_api \
	comfy_api_nodes comfy_config comfy_execution comfy_extras \
	middleware utils; do
	cp -a "$d" %{buildroot}%{_datadir}/comfyui/
done
install -m 644 alembic.ini comfyui_version.py cuda_malloc.py \
	execution.py folder_paths.py hook_breaker_ac10a0.py \
	latent_preview.py main.py node_helpers.py nodes.py \
	protocol.py server.py \
	%{buildroot}%{_datadir}/comfyui/
find %{buildroot}%{_datadir}/comfyui -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find %{buildroot}%{_datadir}/comfyui -type d -name 'tests' -exec rm -rf {} + 2>/dev/null || true

install -d %{buildroot}%{_sysconfdir}/comfyui
install -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/comfyui/extra_model_paths.yaml
install -d %{buildroot}%{_datadir}/comfyui-custom-nodes

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/comfyui <<'EOF'
#!/bin/sh
# ComfyUI. Per-user state in $XDG_DATA_HOME/comfyui.
LIBDIR=%{_datadir}/comfyui
BASE="${COMFYUI_BASE_DIRECTORY:-${XDG_DATA_HOME:-$HOME/.local/share}/comfyui}"
mkdir -p "$BASE/output" "$BASE/input" "$BASE/temp" "$BASE/user" \
	"$BASE/custom_nodes" "$BASE/models"
# Distro custom-node packages live under /usr/share/comfyui-custom-nodes.
# Symlink them into the per-user tree unless the user already has a
# real checkout of the same name.
SYS_NODES="%{_datadir}/comfyui-custom-nodes"
if [ -d "$SYS_NODES" ]; then
	for n in "$SYS_NODES"/*; do
		[ -e "$n" ] || continue
		dest="$BASE/custom_nodes/$(basename "$n")"
		if [ -L "$dest" ] || [ ! -e "$dest" ]; then
			ln -sfn "$n" "$dest"
		fi
	done
fi
export PYTHONPATH="$LIBDIR${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
EXTRA="%{_sysconfdir}/comfyui/extra_model_paths.yaml"
USER_EXTRA="${XDG_CONFIG_HOME:-$HOME/.config}/comfyui/extra_model_paths.yaml"
set -- --base-directory "$BASE" --extra-model-paths-config "$EXTRA" "$@"
if [ -r "$USER_EXTRA" ]; then
	set -- --extra-model-paths-config "$USER_EXTRA" "$@"
fi
cd "$LIBDIR" || exit 1
exec python "$LIBDIR/main.py" "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/comfyui

sed -i '1s|^#!/usr/bin/env python3|#!/usr/bin/python|' \
	%{buildroot}%{_datadir}/comfyui/main.py 2>/dev/null || true

%files
%license LICENSE
%doc README.md QUANTIZATION.md
%{_bindir}/comfyui
%{_datadir}/comfyui/
%dir %{_datadir}/comfyui-custom-nodes
%config(noreplace) %{_sysconfdir}/comfyui/extra_model_paths.yaml
%dir %{_sysconfdir}/comfyui
