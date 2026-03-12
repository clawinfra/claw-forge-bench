"""Unit tests for ablation config definitions."""
import sys
import tempfile
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bench.config import CONFIGS, all_configs, generate_claw_forge_yaml, get_config
from bench.models import ConfigID


def test_five_configs_exist():
    """All 5 ablation configs should be defined."""
    assert len(CONFIGS) == 5
    for cid in ConfigID:
        assert cid in CONFIGS


def test_config_a_baseline():
    """Config A should be str_replace only with no extras."""
    a = get_config(ConfigID.A)
    assert a.edit_mode == "str_replace"
    assert a.loop_detect_threshold == 0
    assert a.verify_on_exit is False


def test_config_b_hashline():
    """Config B should be hashline only."""
    b = get_config(ConfigID.B)
    assert b.edit_mode == "hashline"
    assert b.loop_detect_threshold == 0
    assert b.verify_on_exit is False


def test_config_c_loop_detect():
    """Config C should be str_replace + loop-detect."""
    c = get_config(ConfigID.C)
    assert c.edit_mode == "str_replace"
    assert c.loop_detect_threshold == 5
    assert c.verify_on_exit is False


def test_config_d_verify():
    """Config D should be str_replace + verify-on-exit."""
    d = get_config(ConfigID.D)
    assert d.edit_mode == "str_replace"
    assert d.loop_detect_threshold == 0
    assert d.verify_on_exit is True


def test_config_e_full_stack():
    """Config E should have all three features."""
    e = get_config(ConfigID.E)
    assert e.edit_mode == "hashline"
    assert e.loop_detect_threshold == 5
    assert e.verify_on_exit is True


def test_all_configs_order():
    """all_configs() should return A through E in order."""
    configs = all_configs()
    assert len(configs) == 5
    assert [c.id for c in configs] == list(ConfigID)


def test_to_cli_flags():
    """CLI flags should reflect config settings."""
    a = get_config(ConfigID.A)
    flags = a.to_cli_flags()
    assert "--edit-mode" in flags
    assert "str_replace" in flags
    assert "--no-verify-on-exit" in flags

    e = get_config(ConfigID.E)
    flags = e.to_cli_flags()
    assert "hashline" in flags
    assert "--verify-on-exit" in flags
    assert "--loop-detect-threshold" in flags
    assert "5" in flags


def test_to_yaml_overrides():
    """YAML overrides should contain the right agent settings."""
    b = get_config(ConfigID.B)
    overrides = b.to_yaml_overrides()
    assert overrides["agent"]["edit_mode"] == "hashline"
    assert overrides["agent"]["loop_detect_threshold"] == 0
    assert overrides["agent"]["verify_on_exit"] is False


def test_generate_yaml():
    """generate_claw_forge_yaml should merge base + overrides."""
    base_yaml = PROJECT_ROOT / "configs" / "base.yaml"
    config = get_config(ConfigID.E)

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
        output_path = f.name

    generate_claw_forge_yaml(str(base_yaml), config, output_path)

    with open(output_path) as f:
        result = yaml.safe_load(f)

    assert result["agent"]["edit_mode"] == "hashline"
    assert result["agent"]["loop_detect_threshold"] == 5
    assert result["agent"]["verify_on_exit"] is True
    # Base settings preserved
    assert "pool" in result
    assert result["pool"]["strategy"] == "priority"

    Path(output_path).unlink()
