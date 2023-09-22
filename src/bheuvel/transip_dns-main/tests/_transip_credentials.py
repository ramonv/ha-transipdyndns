# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""TransIP credentials and test domain for performing tests."""
from pathlib import Path


transip_key_file = str(
    Path(f"{__file__}/../../../private_in_root_of_this_repo.key").resolve()
)
transip_user = "john"
transip_domain = "example.com"
