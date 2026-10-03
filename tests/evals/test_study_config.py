"""Pin consumers to the committed study configuration."""

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
    """The results section names the provisioned bucket, region and prefix."""
    results = sc.load_study_config().results
    assert (results.bucket, results.region) == (BUCKET, "us-west-2")
    # Keys begin with the experiment at the bucket root.
    assert results.base_prefix == ""


def test_fleet_section_carries_the_regions_and_the_tag_vocabulary() -> None:
    """The fleet section carries the three regions and both tag forms."""
    fleet = sc.load_study_config().fleet
    assert fleet.regions == ("us-east-1", "us-east-2", "us-west-2")
    assert fleet.tag_prefix == "scaling-"
    assert fleet.standalone_tag == "induction-scaling"


def test_the_roster_is_exactly_the_non_smoke_deploy_specs() -> None:
    """The roster is exactly `EC2_DEPLOY_SPECS` minus the smoke entry: 21 keys."""
    assert sorted(sc.roster_keys()) == sorted(set(EC2_DEPLOY_SPECS) - {SMOKE_KEY})
    assert len(sc.roster_keys()) == 21


def test_families_partition_the_roster_in_ladder_order() -> None:
    """Seven three-rung families flatten to the roster, in roster order."""
    families = sc.load_study_config().roster.families
    assert len(families) == 7
    assert all(len(rungs) == 3 for rungs in families.values())
    flat = tuple(key for rungs in families.values() for key in rungs)
    assert flat == sc.roster_keys()


def test_tag_for_is_total_over_the_roster_and_injective() -> None:
    """Roster tags are unique and an unknown key raises `KeyError`."""
    tags = [sc.tag_for(key) for key in sc.roster_keys()]
    assert len(set(tags)) == len(tags)
    with pytest.raises(KeyError):
        sc.tag_for("not-a-checkpoint")


def test_load_study_config_is_cached() -> None:
    """Repeated loads return the same parsed object."""
    assert sc.load_study_config() is sc.load_study_config()


def test_the_config_reads_no_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The config is identical with and without the S3 and fleet variables set.

    Environment precedence belongs to consumers, not to the cached config.
    """
    before = sc.load_study_config()
    monkeypatch.setenv("EC2_REGIONS", "eu-west-1")
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://somebody-elses-bucket")
    after = sc.load_study_config()
    assert after.fleet.regions == before.fleet.regions
    assert after.results.bucket == before.results.bucket


def test_ec2_default_regions_are_built_from_the_config() -> None:
    """EC2's default regions are ``AWS_REGION`` then the configured fleet."""
    regions = sc.load_study_config().fleet.regions
    assert ec2._DEFAULT_REGIONS == ",".join(dict.fromkeys((ec2.AWS_REGION, *regions)))
    for region in regions:
        assert region in ec2.EC2_REGIONS


def test_the_toml_is_declared_as_package_data() -> None:
    """The TOML is package data, so non-editable installs ship it."""
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

[study]
n_replicates = 30
base_seed = 0
n_harmonics = 9

[analysis]
seed = 0
alpha = 0.05
power_targets = [0.80, 0.90]
equivalence_deltas = [0.10, 0.15, 0.20]
"""


def write_config(tmp_path: Path, text: str) -> Path:
    """Write a study-config TOML for `load_study_config` to read.

    Parameters
    ----------
    tmp_path : Path
        Per-test directory the file is written into.
    text : str
        TOML document to write, usually a mutation of `GOOD_TOML`.

    Returns
    -------
    Path
        The written ``study_config.toml``.
    """
    path = tmp_path / "study_config.toml"
    path.write_text(text)
    return path


def test_a_well_formed_file_loads(tmp_path: Path) -> None:
    """`GOOD_TOML` parses and every section round-trips to its dataclass."""
    cfg = sc.load_study_config(write_config(tmp_path, GOOD_TOML))
    assert cfg.results.bucket == "b"
    assert cfg.roster.families["fam"] == ("a", "b")
    assert cfg.roster.tags["b"] == "b_tag"
    assert cfg.roster.n_rungs == 2
    assert cfg.study == sc.StudyParams(n_replicates=30, base_seed=0, n_harmonics=9)
    assert cfg.analysis == sc.AnalysisParams(
        seed=0,
        alpha=0.05,
        power_targets=(0.80, 0.90),
        equivalence_deltas=(0.10, 0.15, 0.20),
    )


def test_a_checkpoint_cannot_appear_in_two_families(tmp_path: Path) -> None:
    """Reject family overlap even when every checkpoint has a unique tag."""
    duplicate_families = GOOD_TOML.replace(
        'fam = ["a", "b"]',
        'fam = ["a", "b"]\nother = ["b", "c"]',
    ).replace('b = "b_tag"', 'b = "b_tag"\nc = "c_tag"')
    with pytest.raises(ValueError, match="more than one"):
        sc.load_study_config(write_config(tmp_path, duplicate_families))


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
        # Every family has the same number of rungs.
        (
            lambda t: t.replace(
                'fam = ["a", "b"]', 'fam = ["a", "b"]\nsolo = ["c"]'
            ).replace('b = "b_tag"', 'b = "b_tag"\nc = "c_tag"'),
            "unequal rung counts",
        ),
        # A ladder needs two rungs to contrast.
        (
            lambda t: t.replace('fam = ["a", "b"]', 'fam = ["a"]').replace(
                'b = "b_tag"\n', ""
            ),
            "at least two rungs",
        ),
        # The roster needs a family.
        (
            lambda t: t.replace('fam = ["a", "b"]\n', "")
            .replace('a = "a_tag"\n', "")
            .replace('b = "b_tag"\n', ""),
            "no family",
        ),
        # Study parameters are positive integers.
        (lambda t: t.replace("n_replicates = 30", "n_replicates = 0"), "n_replicates"),
        # Seeds are non-negative integers; ``true`` is a typo, not a seed.
        (lambda t: t.replace("seed = 0\nalpha", "seed = -1\nalpha"), "seed"),
        (lambda t: t.replace("seed = 0\nalpha", "seed = true\nalpha"), "seed"),
        (lambda t: t.replace("base_seed = 0", "base_seed = -1"), "base_seed"),
        # Alpha is a probability.
        (lambda t: t.replace("alpha = 0.05", "alpha = 1.5"), "alpha"),
        # Power levels ascend.
        (lambda t: t.replace("[0.80, 0.90]", "[0.90, 0.80]"), "power_targets"),
        # Levels are probabilities and the list is non-empty.
        (lambda t: t.replace("[0.10, 0.15, 0.20]", "[0.10, 1.5]"), "in (0, 1)"),
        (lambda t: t.replace("[0.10, 0.15, 0.20]", "[]"), "equivalence_deltas"),
        # The sizing tables print exactly two power columns.
        (lambda t: t.replace("[0.80, 0.90]", "[0.80]"), "exactly two"),
    ],
)
def test_a_malformed_config_raises_naming_the_defect(
    tmp_path: Path,
    mutation: Callable[[str], str],
    expected: str,
) -> None:
    """Each malformed entry raises `ValueError` naming the offending key."""
    with pytest.raises(ValueError) as exc:
        sc.load_study_config(write_config(tmp_path, mutation(GOOD_TOML)))
    assert expected in str(exc.value)


# results_store consumers.


def test_the_default_results_uri_is_rendered_from_the_config() -> None:
    """The default results URI is ``s3://`` plus the configured bucket."""
    from smolbench.evals.results_store import default_results_uri

    assert default_results_uri() == f"s3://{BUCKET}"


def test_sync_down_names_the_default_uri_when_the_env_is_unset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unconfigured sync fails naming the default URI it needed."""
    from smolbench.evals.results_store import default_results_uri, sync_down

    monkeypatch.delenv("SMOLBENCH_RESULTS_S3", raising=False)
    with pytest.raises(RuntimeError) as exc:
        sync_down(tmp_path / "results", {})
    assert default_results_uri() in str(exc.value)
