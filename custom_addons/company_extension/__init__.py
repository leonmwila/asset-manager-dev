from . import models
from . import wizard


def _generate_grz_numbers(env):
    """Post-init hook to generate GRZ numbers for all existing serial ranges"""
    env['grz.available.number'].generate_all_missing_numbers()
