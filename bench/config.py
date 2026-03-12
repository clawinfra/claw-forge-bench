"""Ablation configuration definitions."""
from __future__ import annotations

from pathlib import Path

import yaml

from bench.models import AblationConfig, ConfigID

# ── The 5 Ablation Configs ──────────────────────────────────────────────

CONFIGS: dict[ConfigID, AblationConfig] = {
    ConfigID.A: AblationConfig(
        id=ConfigID.A,
        label="baseline (str_replace only)",
        edit_mode="str_replace",
        loop_detect_threshold=0,
        verify_on_exit=False,
    ),
    ConfigID.B: AblationConfig(
        id=ConfigID.B,
        label="hashline",
        edit_mode="hashline",
        loop_detect_threshold=0,
        verify_on_exit=False,
    ),
    ConfigID.C: AblationConfig(
        id=ConfigID.C,
        label="str_replace + loop-detect",
        edit_mode="str_replace",
        loop_detect_threshold=5,
        verify_on_exit=False,
    ),
    ConfigID.D: AblationConfig(
        id=ConfigID.D,
        label="str_replace + verify-on-exit",
        edit_mode="str_replace",
        loop_detect_threshold=0,
        verify_on_exit=True,
    ),
    ConfigID.E: AblationConfig(
        id=ConfigID.E,
        label="hashline + loop-detect + verify-on-exit",
        edit_mode="hashline",
        loop_detect_threshold=5,
        verify_on_exit=True,
    ),
}


def get_config(config_id: ConfigID) -> AblationConfig:
    """Return the AblationConfig for the given ID."""
    return CONFIGS[config_id]


def all_configs() -> list[AblationConfig]:
    """Return all 5 configs in order A→E."""
    return [CONFIGS[cid] for cid in ConfigID]


def generate_claw_forge_yaml(
    base_yaml_path: str,
    config: AblationConfig,
    output_path: str,
) -> None:
    """Merge ablation overrides into base.yaml and write to output_path.

    The base.yaml contains shared provider pool config.
    The config overrides agent.edit_mode, agent.loop_detect_threshold,
    and agent.verify_on_exit.
    """
    base_path = Path(base_yaml_path)
    with open(base_path) as f:
        base = yaml.safe_load(f)

    overrides = config.to_yaml_overrides()
    # Deep merge the agent section
    if "agent" not in base:
        base["agent"] = {}
    base["agent"].update(overrides["agent"])

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        yaml.dump(base, f, default_flow_style=False, sort_keys=False)
