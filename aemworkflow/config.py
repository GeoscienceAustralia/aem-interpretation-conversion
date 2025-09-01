import os

def get_ogr_path():
    return "ogr2ogr.exe" if os.name == 'nt' else "ogr2ogr"