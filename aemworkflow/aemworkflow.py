import sys

import click

from .conversion import main as conversion
from .exports import main as exports
from .interpretation import main as interpretation
from .pre_interpretation import main as pre_interpretation
from .validation import main as validation


@click.group()
def cli():
    """AEM Interpretation Conversion CLI."""
    pass


@cli.command()
@click.option("--i", "input_directory", type=click.Path(exists=True), required=True)
@click.option("--o", "output_directory", type=click.Path(), required=True)
@click.option("--crs", default="28349", help="Coordinate Reference System (default: EPSG:28349)")
@click.option("--gis", default="esri_arcmap_0.5", help="GIS format (default: esri_arcmap_0.5)")
@click.option("--lines", default=10, help="Number of depth lines (default: 10)")
@click.option("--lines_increment", default=30, help="Depth lines increment (default: 30)")
def pre_interpret(input_directory, output_directory, crs, gis="esri_arcmap_0.5", lines=10, lines_increment=30):
    try:
        pre_interpretation(input_directory, output_directory, crs, gis, lines, lines_increment)
        click.echo("Completed pre-interpretation")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--i", "input_directory", type=click.Path(exists=True), required=True)
@click.option("--o", "output_directory", type=click.Path(), required=True)
@click.option("--crs", default="28349", help="Coordinate Reference System (default: EPSG:28349)")
@click.option("--gis", default="esri_arcmap_0.5", help="GIS format (default: esri_arcmap_0.5)")
@click.option("--lines", default=10, help="Number of depth lines (default: 10)")
@click.option("--lines_increment", default=30, help="Depth lines increment (default: 30)")
def interpret(input_directory, output_directory, crs="28349", gis="esri_arcmap_0.5", lines=10, lines_increment=30):
    try:
        interpretation(input_directory, output_directory, crs, gis, lines, lines_increment)
        click.echo("Completed interpretation")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--i", "input_directory", type=click.Path(exists=True), required=True)
@click.option("--o", "output_directory", type=click.Path(), required=True)
@click.option("--a", "asud_filename", type=click.Path(exists=True), required=True)
@click.option("--c", "confidence_filename", type=click.Path(exists=True), required=True)
@click.option("--ct", "contact_filename", type=click.Path(exists=True), required=True)
@click.option("--ib", "interp_filename", type=click.Path(exists=True), required=True)
@click.option("--cenozoic", type=click.Path(exists=True), required=False)
@click.option("--mesozoic", type=click.Path(exists=True), required=False)
@click.option("--paleozoic", type=click.Path(exists=True), required=False)
@click.option("--neoproterozoic", type=click.Path(exists=True), required=False)
@click.option("--mesoproterozoic", type=click.Path(exists=True), required=False)
@click.option("--paleoproterozoic", type=click.Path(exists=True), required=False)
@click.option("--archean", type=click.Path(exists=True), required=False)
def validate(input_directory, output_directory, asud_filename, confidence_filename, contact_filename, interp_filename,
             cenozoic, mesozoic, paleozoic, neoproterozoic, mesoproterozoic, paleoproterozoic, archean):
    try:
        asud_era_file_paths = {
            'Cenozoic': cenozoic,
            'Mesozoic': mesozoic,
            'Paleozoic': paleozoic,
            'Neoproterozoic': neoproterozoic,
            'Mesoproterozoic': mesoproterozoic,
            'Paleoproterozoic': paleoproterozoic,
            'Archean': archean,
        }

        asud_era_file_paths = {era: path for era, path in asud_era_file_paths.items() if path}

        validation(input_directory, output_directory, asud_filename, confidence_filename, contact_filename,
                   interp_filename, asud_era_file_paths)
        click.echo("Completed validation")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--i", "input_directory", type=click.Path(exists=True), required=True)
@click.option("--o", "output_directory", type=click.Path(), required=True)
@click.option("--crs", default="28349", help="Coordinate Reference System (default: EPSG:28349)")
def convert(input_directory, output_directory, crs):
    try:
        conversion(input_directory, output_directory, crs)
        click.echo("Completed conversion")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--i", "input_directory", type=click.Path(exists=True), required=True)
@click.option("--o", "output_directory", type=click.Path(), required=True)
@click.option("--b", "boundary_filename", type=click.Path(exists=True), required=True)
@click.option("--s", "split_filename", type=click.Path(exists=True), required=True)
@click.option("--mdc", is_flag=True, help="Export to MDC format", default=False)
@click.option("--mdch", is_flag=True, help="Export to MDCH format", default=False)
@click.option("--csv", is_flag=True, help="Export to CSV format", default=False)
@click.option("--es", is_flag=True, help="Export to GA Portal / Earth Sciences format", default=False)
@click.option("--3d", "export_3d", is_flag=True, help="Export to 3D shape file format", default=False)
@click.option("--crs", default="28349", help="Coordinate Reference System (default: EPSG:28349)")
def export(input_directory, output_directory, boundary_filename, split_filename, mdc, mdch, csv, es, export_3d, crs):
    try:
        exports(input_directory, output_directory, boundary_filename, split_filename,
                mdc, mdch, csv, es, export_3d, crs)
        click.echo("Completed export")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
