import sys
import click
from aemworkflow.conversion import main as conversion

@click.group()
def cli():
    """AEM Interpretation Conversion CLI."""
    pass

@cli.command()
@click.argument("input_directory", type=click.Path(exists=True))
@click.argument("output_directory", type=click.Path())
@click.option("--crs", default="28349", help="Coordinate Reference System (default: EPSG:28349)")
def convert(input_directory, output_directory, crs):
    """Convert an AEM interpretation file to a different format."""
    try:
        conversion(input_directory, output_directory, crs)
        click.echo(f"Comleted conversion")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)