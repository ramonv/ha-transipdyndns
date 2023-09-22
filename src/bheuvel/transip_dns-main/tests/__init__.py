# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Collection of tests.

Unit tests
Integration tests;
    against the actual TransIP REST API will succeed if the call is
    correct, but it will not actually create/delete/modify anything
    creates, and therefore cannot be fully verified to work.
Functional tests, against the actual TransIP REST API, but requires real credentials.
    It mostly performs the same tests as the integration tests, but will
    also verify if records are actually created, modified and raise
    errors if records are not removed.
"""

try:
    transip_demo_token = None
    from tests.transip_credentials import (  # noqa
        transip_user,
        transip_key_file,
        transip_domain,
    )

except ImportError:  # pragma: not live account skip live coverage
    print("missing authentication information needed to run tests")
    print(f"Create the file '{__path__[0]}/transip_credentials.py', with content:")
    print('transip_user = "userlogin"')
    print("transip_key_file = /home/keys/transip.key")
    print('transip_domain = "example.com"')
    print("Skipping mosts tests due to absence of credentials")
    transip_user = None
    transip_key_file = None
    transip_domain = "transipdemonstratie.nl"
    transip_demo_token = (
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImN3MiFSbDU2eDNoUnkjelM4YmdOIn0.e"
        "yJpc3MiOiJhcGkudHJhbnNpcC5ubCIsImF1ZCI6ImFwaS50cmFuc2lwLm5sIiwianRpIjoiY3cyIV"
        "JsNTZ4M2hSeSN6UzhiZ04iLCJpYXQiOjE1ODIyMDE1NTAsIm5iZiI6MTU4MjIwMTU1MCwiZXhwIjo"
        "yMTE4NzQ1NTUwLCJjaWQiOiI2MDQ0OSIsInJvIjpmYWxzZSwiZ2siOmZhbHNlLCJrdiI6dHJ1ZX0."
        "fYBWV4O5WPXxGuWG-vcrFWqmRHBm9yp0PHiYh_oAWxWxCaZX2Rf6WJfc13AxEeZ67-lY0TA2kSaOC"
        "p0PggBb_MGj73t4cH8gdwDJzANVxkiPL1Saqiw2NgZ3IHASJnisUWNnZp8HnrhLLe5ficvb1D9WOU"
        "OItmFC2ZgfGObNhlL2y-AMNLT4X7oNgrNTGm-mespo0jD_qH9dK5_evSzS3K8o03gu6p19jxfsnIh"
        "8TIVRvNdluYC2wo4qDl5EW5BEZ8OSuJ121ncOT1oRpzXB0cVZ9e5_UVAEr9X3f26_Eomg52-Pjrgc"
        "RJ_jPIUYbrlo06KjjX2h0fzMr21ZE023Gw"
    )
