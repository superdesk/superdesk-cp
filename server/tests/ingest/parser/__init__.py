
import os


def get_fixture_path(filename, provider):
    return os.path.join(
        os.path.dirname(__file__),
        'fixtures',
        provider,
        filename,
    )
