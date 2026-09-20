"""Fixtures pinned by three test files so the production template stays one copy."""

import string

from smolbench.induction.periodic import CONDITIONS

# Covers every generator placeholder.
PERIODIC_TMPL = string.Template(
    "CTX:\n$positive_info\nQ: How many of positions 1..$seq_len include '$label'?"
)

#: Excludes ``zero``, which requires a range-free template.
POSITIVE_ARMS = {name: c for name, c in CONDITIONS.items() if not c.omit_range}
