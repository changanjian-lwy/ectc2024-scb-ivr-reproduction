# LTspice result validation

These modules parse locally generated LTspice logs and lock accepted results or
accepted failures to their declared experiment boundaries. They are separate
from the reusable model package because the `.log` inputs are machine-generated
and intentionally excluded from Git.

`two_branch_revalidation.py` aggregates the P24 target branch and the explicitly
labelled P25-derived branches. `r04*_regression.py` files each validate one
recorded experiment family.
