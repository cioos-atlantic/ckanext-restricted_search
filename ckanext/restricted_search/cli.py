"""
Code primarily adapted from vitality_model.py, which was used with paster commands for earlier versions of ckan
"""
import click

def get_commands():
    return[restricted_search]

"""
    Utility commands to manage the restricted search function.
    May not be needed in a refactor, but for now is required to run
"""

CMD_ARG = 0
MIN_ARGS = 1

@click.group()
@click.pass_context
def restricted_search(ctx):

    pass
