import pytest
from tests.unit.conftest import environment_generator, parameters_generator


@pytest.mark.parametrize(
    "params, parameters, variables",
    [
        (
            [
                "user",
                "private_key",
                "domainname",
                "record_name",
                "record_type",
                "record_ttl",
                "record_data",
                "log",
            ],
            16,
            8,
        ),
        (["query_ipv4", "query_ipv6", "delete"], 3, 3),
    ],
)
def test_get_variables(params: list, parameters: int, variables: int):
    """Simple test for the environment and parameter generators.

    Args:
        params (list): Requested test options
        parameters (int): Expected number of items in the command line (sys.argv)
        variables (int): Expected number of items for environment variables

    The generators will produce the test data for the requested options. Usually a key and a value.

    So requesting n options will ususally result in n*2 items,

    A regular command line (sys.argv) also contains the program itself,
    therefore for command line it will be (n*2)+1
    Exception to this are the switches without value (query_ipv4, query_ipv6)

    For environment variables it will always be n*2

    """
    env = environment_generator(params=params)
    pars = parameters_generator(params=params)

    assert len(pars) == parameters + 1
    assert len(env) == variables
