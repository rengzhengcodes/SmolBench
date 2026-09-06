"""The committed study config: roster, results bucket, regions, fleet tag prefix.

``smolbench/evals/study_config.toml`` is meant to be the ONE place the 21-model
roster, the results bucket and the fleet's regions/tag prefix are written down;
these tests pin every slice-2 consumer against it, so a table that drifts away
from the file fails here rather than on a billing box.
"""

import tomllib

import pytest

from smolbench.evals import study_config as sc
from smolbench.evals.providers import ec2
from smolbench.evals.providers.ec2 import EC2_DEPLOY_SPECS
from tests._paths import REPO_ROOT

#: The smoke entry exercises the lifecycle on one cheap GPU; it is not a rung
#: of the family ladder, so it is the one deploy spec outside the roster.
SMOKE_KEY = "qwen2.5-1.5b"

#: Provisioned by ``scripts/results/provision_results_bucket.py`` (see
#: ``smolbench/evals/README.md``) and named in ``notebooks/ARCHIVE.md``.
BUCKET = "smolbench-results-414266451290"


@pytest.fixture(autouse=True)
def _no_ambient_env(monkeypatch):
    """The config must not depend on a developer shell's exported variables."""
    for var in ("SMOLBENCH_RESULTS_S3", "SMOLBENCH_RESULTS_S3_REGION",
                "EC2_REGIONS", "AWS_REGION"):
        monkeypatch.delenv(var, raising=False)


def test_results_section_names_the_provisioned_bucket():
    """[results] carries the bucket/region the runbook actually provisioned."""
    results = sc.load_study_config().results
    assert (results.bucket, results.region) == (BUCKET, "us-west-2")
    # The live log sits at the bucket root: keys start with <experiment>/.
    assert results.base_prefix == ""


def test_fleet_section_carries_the_regions_and_the_tag_vocabulary():
    """[fleet] owns the spot-capacity regions and both experiment-tag spellings."""
    fleet = sc.load_study_config().fleet
    assert fleet.regions == ("us-east-1", "us-east-2", "us-west-2")
    assert fleet.tag_prefix == "scaling-"
    assert fleet.standalone_tag == "induction-scaling"


def test_the_roster_is_exactly_the_non_smoke_deploy_specs():
    """C1's pin: [roster] and EC2_DEPLOY_SPECS name the same 21 checkpoints."""
    assert sorted(sc.roster_keys()) == sorted(set(EC2_DEPLOY_SPECS) - {SMOKE_KEY})
    assert len(sc.roster_keys()) == 21


def test_families_partition_the_roster_in_ladder_order():
    """7 families x 3 rungs, concatenating to ``roster_keys()`` in that order."""
    families = sc.families()
    assert len(families) == 7
    assert all(len(rungs) == 3 for rungs in families.values())
    flat = tuple(key for rungs in families.values() for key in rungs)
    assert flat == sc.roster_keys()


def test_tag_for_is_total_over_the_roster_and_injective():
    """Every roster key has its own short analysis tag; an unknown key raises."""
    tags = [sc.tag_for(key) for key in sc.roster_keys()]
    assert len(set(tags)) == len(tags)
    with pytest.raises(KeyError):
        sc.tag_for("not-a-checkpoint")


def test_load_study_config_is_cached():
    """Repeated loads return the SAME object: no re-parse per consumer import."""
    assert sc.load_study_config() is sc.load_study_config()


def test_the_config_reads_no_environment(monkeypatch):
    """Env precedence belongs to each consumer, not to the cached config object.

    Baking ``EC2_REGIONS``/``SMOLBENCH_RESULTS_S3`` into the cached object would
    freeze whichever value the first importer happened to see -- and ``ec2``
    freezes its constants at import while ``results_store`` reads at call time,
    so the two would silently disagree.
    """
    before = sc.load_study_config()
    monkeypatch.setenv("EC2_REGIONS", "eu-west-1")
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://somebody-elses-bucket")
    after = sc.load_study_config()
    assert after.fleet.regions == before.fleet.regions
    assert after.results.bucket == before.results.bucket


def test_ec2_default_regions_are_built_from_the_config():
    """``ec2._DEFAULT_REGIONS`` is the config's region list, not a second copy.

    ``AWS_REGION`` still leads (a caller's own region is tried first) and the
    ``EC2_REGIONS`` environment override is unchanged -- this pins only where
    the DEFAULT comes from.
    """
    regions = sc.load_study_config().fleet.regions
    assert ec2._DEFAULT_REGIONS == ",".join(
        dict.fromkeys((ec2.AWS_REGION, *regions))
    )
    for region in regions:
        assert region in ec2.EC2_REGIONS


def test_the_toml_is_declared_as_package_data():
    """A non-editable install must ship the .toml, or every consumer dies at import.

    ``include-package-data = false`` in pyproject means setuptools picks up
    ``*.py`` only; the config file needs an explicit package-data entry.
    """
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    package_data = pyproject["tool"]["setuptools"]["package-data"]
    assert "*.toml" in package_data["smolbench.evals"]


# ---------------------------------------------------------------------------
# Validation: a malformed config must fail loudly at load, never half-load
# ---------------------------------------------------------------------------

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


def write_config(tmp_path, text):
    path = tmp_path / "study_config.toml"
    path.write_text(text)
    return path


def test_a_well_formed_file_loads(tmp_path):
    """The fixture text below is a VALID config, so the rejection cases that
    follow are rejected for the mutation they carry and not for some other
    defect they all share."""
    cfg = sc.load_study_config(write_config(tmp_path, GOOD_TOML))
    assert cfg.results.bucket == "b"
    assert cfg.roster.families["fam"] == ("a", "b")
    assert cfg.roster.tags["b"] == "b_tag"


@pytest.mark.parametrize(
    "mutation, expected",
    [
        # A whole section missing.
        (lambda t: t.replace("[fleet]", "[fleet_typo]"), "fleet"),
        # A key missing from a section.
        (lambda t: t.replace('tag_prefix = "scaling-"\n', ""), "tag_prefix"),
        # A family naming a checkpoint with no tag: tag_for would KeyError
        # somewhere downstream instead of here.
        (lambda t: t.replace('fam = ["a", "b"]', 'fam = ["a", "c"]'), "c"),
        # A tag for a checkpoint no family lists: a rung silently unrun.
        (lambda t: t.replace('b = "b_tag"', 'b = "b_tag"\nz = "z_tag"'), "z"),
        # Two checkpoints sharing one analysis tag: two lanes' results would
        # land in one directory.
        (lambda t: t.replace('b = "b_tag"', 'b = "a_tag"'), "a_tag"),
    ],
)
def test_a_malformed_config_raises_naming_the_defect(tmp_path, mutation, expected):
    """Every structural defect raises at LOAD, with the offending name in the message."""
    with pytest.raises(ValueError) as exc:
        sc.load_study_config(write_config(tmp_path, mutation(GOOD_TOML)))
    assert expected in str(exc.value)


# ---------------------------------------------------------------------------
# results_store consumers
# ---------------------------------------------------------------------------

def test_the_default_results_uri_is_rendered_from_the_config():
    """The canonical ``s3://...`` spelling has ONE home, not a literal per script."""
    from smolbench.evals.results_store import default_results_uri

    assert default_results_uri() == f"s3://{BUCKET}"


def test_sync_down_names_the_default_uri_when_the_env_is_unset(tmp_path, monkeypatch):
    """The "nothing to sync" error tells the operator exactly what to export."""
    from smolbench.evals.results_store import default_results_uri, sync_down

    monkeypatch.delenv("SMOLBENCH_RESULTS_S3", raising=False)
    with pytest.raises(RuntimeError) as exc:
        sync_down(tmp_path / "results", {})
    assert default_results_uri() in str(exc.value)
