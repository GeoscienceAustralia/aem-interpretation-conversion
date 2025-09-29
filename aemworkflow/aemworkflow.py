import sys
import click
from .conversion import main as conversion
from .validation import main as validation
from .pre_interpretation import main as pre_interpretation
from .interpretation import main as interpretation
from .exports import main as exports

@click.group()
def cli():
    """AEM Interpretation Conversion CLI."""
    pass

@cli.command()
@click.argument("--i", "input_directory", type=click.Path(exists=True))
@click.argument("--o", "output_directory", type=click.Path())
@click.option("--crs", default="28349", help="Coordinate Reference System (default: EPSG:28349)")
@click.option("--gis", default="esri_arcmap_0.5", help="GIS format (default: esri_arcmap_0.5)")
@click.option("--lines", default=10, help="Number of depth lines (default: 10)")
@click.option("--lines_increment", default=30, help="Depth lines increment (default: 30)")
def pre_interpret(input_directory, output_directory, crs, gis="esri_arcmap_0.5", lines=10, lines_increment=30):
    try:
        pre_interpretation(input_directory, output_directory, crs, gis, lines, lines_increment)
        click.echo(f"Completed pre-interpretation")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument("--i", "input_directory", type=click.Path(exists=True))
@click.argument("--o", "output_directory", type=click.Path())
@click.option("--crs", default="28349", help="Coordinate Reference System (default: EPSG:28349)")
@click.option("--gis", default="esri_arcmap_0.5", help="GIS format (default: esri_arcmap_0.5)")
@click.option("--lines", default=10, help="Number of depth lines (default: 10)")
@click.option("--lines_increment", default=30, help="Depth lines increment (default: 30)")
def interpret(input_directory, output_directory, crs="28349", gis="esri_arcmap_0.5", lines=10, lines_increment=30):
    try:
        interpretation(input_directory, output_directory, crs, gis, lines, lines_increment)
        click.echo(f"Completed interpretation")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument("--i", "input_directory", type=click.Path(exists=True))
@click.argument("--o", "output_directory", type=click.Path())
@click.argument("--a", "asud_filename", type=click.Path(exists=True))
def validate(input_directory, output_directory, asud_filename):
    try:
        validation(input_directory, output_directory, asud_filename)
        click.echo(f"Completed validation")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument("--i", "input_directory", type=click.Path(exists=True))
@click.argument("--o", "output_directory", type=click.Path())
@click.option("--crs", default="28349", help="Coordinate Reference System (default: EPSG:28349)")
def convert(input_directory, output_directory, crs):
    try:
        conversion(input_directory, output_directory, crs)
        click.echo(f"Completed conversion")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument("--i", "input_directory", type=click.Path(exists=True))
@click.argument("--o", "output_directory", type=click.Path())
@click.argument("-b", "boundary_filename", type=click.Path(exists=True))
@click.argument("-s", "split_filename", type=click.Path(exists=True))
@click.option("--mdc", is_flag=True, help="Export to MDC format", default=False)
@click.option("--mdch", is_flag=True, help="Export to MDCH format", default=False)
@click.option("-egs", is_flag=True, help="Export to EGS format", default=False)
def export(input_directory, output_directory, boundary_filename, split_filename, mdc, mdch, egs):
    try:
        exports(input_directory, output_directory, boundary_filename, split_filename, mdc, mdch, egs)
        click.echo(f"Completed export")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
