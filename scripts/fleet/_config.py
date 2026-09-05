"""Constants shared across the ``scripts/fleet/*.py`` family.

This file exists so the study's ``scaling-`` EC2 tag prefix and its default
region list are declared in exactly ONE place, for ``run_fleet.py``,
``fleet_status.py``, ``fleet_teardown.py`` (via ``fleet_status``, which it
already imports) and ``run_shards.py`` to read -- instead of each spelling
its own copy that can silently drift from the others, the way
``fleet_status.SCALING_TAG_PREFIX``/``STATUS_REGIONS`` and
``run_fleet.DEFAULT_REGIONS``/``Lane.experiment_tag`` did before this file
existed, with only a comment (not code) asserting they agreed.

It deliberately has NO imports beyond ``from __future__ import annotations``,
and no AWS dependency, so any of the fleet scripts above can load it at
IMPORT time with no side effects -- ``fleet_status.py`` in particular is
documented as importable with no AWS SDK, for analysis notebooks, and must
stay that way. It is loaded BY FILE PATH, never a bare ``import _config`` or
``from _config import ...`` (see the ``_load_fleet_config`` loader each
consumer defines): ``scripts/fleet`` has no ``__init__.py`` -- it is not a
package -- and every module in it is already loaded under a private module
name by its callers (``tests/tooling/test_run_fleet.py``,
``run_fleet._fleet_status_module``, ``fleet_teardown._fleet_status``), so a
bare import name would be ambiguous at best and simply absent from
``sys.path`` at worst.

NOTE (scope): ``smolbench.evals.providers.ec2._DEFAULT_REGIONS`` is a THIRD,
deliberately DIFFERENT region spelling -- it puts the calling process's own
``AWS_REGION`` first (``",".join(dict.fromkeys((AWS_REGION, "us-east-1",
"us-east-2", "us-west-2")))``), which matters for that module's standalone,
non-fleet callers (e.g. a lone ``notebooks/induction/run_study.py`` launch),
where "closest region first" is the right hunt order. That spelling is out
of scope for this file; do not fold it in here.

Every fleet script now reads these from here: ``fleet_status.py``
(``SCALING_TAG_PREFIX``/``STATUS_REGIONS``), ``run_fleet.py`` (its
``DEFAULT_REGIONS`` constant, ``TIER_REGIONS`` and ``Lane.experiment_tag``),
``run_shards.py`` (via its own ``_load_fleet_config``) and
``fleet_teardown.py`` (transitively, through ``fleet_status``).
"""

from __future__ import annotations

#: Comma-separated, matching every fleet lane's ``EC2_REGIONS`` default (see
#: ``run_fleet.Lane.regions``, which falls back to this for every tier but D).
DEFAULT_REGIONS: str = "us-east-1,us-east-2,us-west-2"

#: Every fleet lane's ``smolbench:experiment`` EC2 tag is
#: ``f"{SCALING_TAG_PREFIX}{spec_key}"`` (see ``run_fleet.Lane.experiment_tag``).
SCALING_TAG_PREFIX: str = "scaling-"

#: `DEFAULT_REGIONS`, split on "," and stripped -- derived FROM the string
#: (rather than declared separately) so the tuple form can never drift from
#: it.
REGION_TUPLE: tuple[str, ...] = tuple(
    region.strip() for region in DEFAULT_REGIONS.split(",") if region.strip()
)
