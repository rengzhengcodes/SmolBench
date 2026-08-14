"""Re-measure response-level facts with a SAFE loader that ignores !!python tags
(no unsafe_load: unknown tags are mapped to plain dicts/strings, never constructed)."""
import yaml
from pathlib import Path

class TagIgnoringLoader(yaml.SafeLoader):
    pass
def _ignore(loader, suffix, node):
    if isinstance(node, yaml.MappingNode):  return loader.construct_mapping(node, deep=True)
    if isinstance(node, yaml.SequenceNode): return loader.construct_sequence(node, deep=True)
    return loader.construct_scalar(node)
TagIgnoringLoader.add_multi_constructor("", _ignore)
TagIgnoringLoader.add_multi_constructor("tag:yaml.org,2002:python/object:", _ignore)

CONDS = ["glm_air_noise_intens","glm_flash_noise_intens","exaone_32b_noise_intens",
         "exaone_33b_noise_intens","min3_8b_noise_intens","min3_14b_noise_intens"]
print(f"{'condition':26s} {'marks':>6s} {'empty':>6s} {'scored':>7s} {'ans_in_resp':>12s} {'maxchars':>10s}")
for cond in CONDS:
    n=empty=scored=hit=0; mx=0
    for f in sorted(Path(f"notebooks/induction/results/{cond}").glob("rep_*.yaml")):
        doc = yaml.load(f.read_text(), Loader=TagIgnoringLoader)
        for m in doc["marks"]:
            n += 1
            resp = m.get("response") or ""
            if not isinstance(resp, str): resp = str(resp)
            mx = max(mx, len(resp))
            if resp.strip() == "": empty += 1
            if m.get("score") == 1: scored += 1
            if str(m.get("answer")) in resp: hit += 1
    print(f"{cond:26s} {n:6d} {empty:6d} {scored:7d} {hit:12d} {mx:10d}")
