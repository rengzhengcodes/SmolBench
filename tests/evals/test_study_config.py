"""Pin consumers to the committed study configuration."""

# pylint: disable=missing-function-docstring,missing-class-docstring

import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest

from smolbench.evals import study_config as sc
from smolbench.evals.providers import ec2
from smolbench.evals.providers.ec2 import EC2_DEPLOY_SPECS
from tests._paths import REPO_ROOT

#: The smoke entry is outside the roster because it is not a family rung.
SMOKE_KEY = "qwen2.5-1.5b"

BUCKET = "smolbench-results-414266451290"


@pytest.fixture(autouse=True)
def _no_ambient_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """The config must not depend on a developer shell's exported variables."""
    for var in (
        "SMOLBENCH_RESULTS_S3",
        "SMOLBENCH_RESULTS_S3_REGION",
        "EC2_REGIONS",
        "AWS_REGION",
    ):
        monkeypatch.delenv(var, raising=False)


def test_results_section_names_the_provisioned_bucket() -> None:
    """Pin the configured results location."""
    results = sc.load_study_config().results
    assert (results.bucket, results.region) == (BUCKET, "us-west-2")
    # Keys begin with the experiment at the bucket root.
    assert results.base_prefix == ""


def test_fleet_section_carries_the_regions_and_the_tag_vocabulary() -> None:
    """Pin fleet regions and tag forms."""
    fleet = sc.load_study_config().fleet
    assert fleet.regions == ("us-east-1", "us-east-2", "us-west-2")
    assert fleet.tag_prefix == "scaling-"
    assert fleet.standalone_tag == "induction-scaling"


def test_the_roster_is_exactly_the_non_smoke_deploy_specs() -> None:
    """Pin roster checkpoints to non-smoke deploy specs."""
    assert sorted(sc.roster_keys()) == sorted(set(EC2_DEPLOY_SPECS) - {SMOKE_KEY})
    assert len(sc.roster_keys()) == 21


def test_families_partition_the_roster_in_ladder_order() -> None:
    """Pin three-rung families in roster order."""
    families = sc.families()
    assert len(families) == 7
    assert all(len(rungs) == 3 for rungs in families.values())
    flat = tuple(key for rungs in families.values() for key in rungs)
    assert flat == sc.roster_keys()


def test_tag_for_is_total_over_the_roster_and_injective() -> None:
    """Require unique roster tags and reject unknown keys."""
    tags = [sc.tag_for(key) for key in sc.roster_keys()]
    assert len(set(tags)) == len(tags)
    with pytest.raises(KeyError):
        sc.tag_for("not-a-checkpoint")


def test_load_study_config_is_cached() -> None:
    """Cache the parsed configuration."""
    assert sc.load_study_config() is sc.load_study_config()


def test_the_config_reads_no_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep environment precedence in consumers, not cached config."""
    before = sc.load_study_config()
    monkeypatch.setenv("EC2_REGIONS", "eu-west-1")
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://somebody-elses-bucket")
    after = sc.load_study_config()
    assert after.fleet.regions == before.fleet.regions
    assert after.results.bucket == before.results.bucket


def test_ec2_default_regions_are_built_from_the_config() -> None:
    """Build default EC2 regions from config with ``AWS_REGION`` first."""
    regions = sc.load_study_config().fleet.regions
    assert ec2._DEFAULT_REGIONS == ",".join(dict.fromkeys((ec2.AWS_REGION, *regions)))
    for region in regions:
        assert region in ec2.EC2_REGIONS


def test_the_toml_is_declared_as_package_data() -> None:
    """Ship the TOML in non-editable installs."""
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    package_data = pyproject["tool"]["setuptools"]["package-data"]
    assert "*.toml" in package_data["smolbench.evals"]


# Malformed config validation.

GOOD_TOML = """
[results]
bucket = "b"
region = "r"
base_prefix = ""

[fleet]
regions = ["us-east-1"]
tag_prefix = "scaling-"
standalone_tag = "induction-scaling"

[roster.families]
fam = ["a", "b"]

[roster.tags]
a = "a_tag"
b = "b_tag"
"""


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "study_config.toml"
    path.write_text(text)
    return path


def test_a_well_formed_file_loads(tmp_path: Path) -> None:
    """Load the unmodified fixture."""
    cfg = sc.load_study_config(write_config(tmp_path, GOOD_TOML))
    assert cfg.results.bucket == "b"
    assert cfg.roster.families["fam"] == ("a", "b")
    assert cfg.roster.tags["b"] == "b_tag"


@pytest.mark.parametrize(
    "mutation, expected",
    [
        # Missing section.
        (lambda t: t.replace("[fleet]", "[fleet_typo]"), "fleet"),
        # Missing key.
        (lambda t: t.replace('tag_prefix = "scaling-"\n', ""), "tag_prefix"),
        # A family checkpoint needs a tag.
        (lambda t: t.replace('fam = ["a", "b"]', 'fam = ["a", "c"]'), "c"),
        # Every tag needs a family checkpoint.
        (lambda t: t.replace('b = "b_tag"', 'b = "b_tag"\nz = "z_tag"'), "z"),
        # Tags must not collide: results share directories.
        (lambda t: t.replace('b = "b_tag"', 'b = "a_tag"'), "a_tag"),
    ],
)
def test_a_malformed_config_raises_naming_the_defect(
    tmp_path: Path,
    mutation: Callable[[str], str],
    expected: str,
) -> None:
    """Name malformed configuration entries."""
    with pytest.raises(ValueError) as exc:
        sc.load_study_config(write_config(tmp_path, mutation(GOOD_TOML)))
    assert expected in str(exc.value)


# results_store consumers.


def test_the_default_results_uri_is_rendered_from_the_config() -> None:
    """Render the configured canonical URI."""
    from smolbench.evals.results_store import default_results_uri

    assert default_results_uri() == f"s3://{BUCKET}"


def test_sync_down_names_the_default_uri_when_the_env_is_unset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Name the required URI when sync is unconfigured."""
    from smolbench.evals.results_store import default_results_uri, sync_down

    monkeypatch.delenv("SMOLBENCH_RESULTS_S3", raising=False)
    with pytest.raises(RuntimeError) as exc:
        sync_down(tmp_path / "results", {})
    assert default_results_uri() in str(exc.value)
