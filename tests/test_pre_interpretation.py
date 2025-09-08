import pytest
from aemworkflow import pre_interpretation
import pandas as pd
import geopandas as gpd
import folium

def test_all_lines_creates_gmt_file(tmp_path):
    # Prepare input path file
    path_file = tmp_path / "test.path.txt"
    path_file.write_text("1 2 3 4 100.0 200.0 7 8 9\n2 3 4 5 110.0 210.0 8 9 10\n")
    output_file = tmp_path / "test.gmt"
    crs = 4326
    gis = None
    mode = 'w'

    pre_interpretation.all_lines(str(path_file), str(output_file), crs, gis, mode)

    content = output_file.read_text()
    assert "# @VGMT1.0 @GLINESTRING" in content
    assert "# FEATURE_DATA" in content
    assert "100.0 200.0" in content
    assert "110.0 210.0" in content

def test_print_boxes_writes_box(tmp_path):
    out_file_path = tmp_path / "box.txt"
    with open(out_file_path, "w") as out_file:
        pre_interpretation.print_boxes(10, 20, 30, 40, out_file, 0.5, 0.5)
    content = out_file_path.read_text()
    assert "# @Dextent" in content
    assert "# @Dupper_left" in content
    assert "# @Dlower_right" in content
    assert "# @Dground_level" in content
    assert ">\n" in content

def test_box_elevation_creates_box_gmt(tmp_path):
    extent_file = tmp_path / "test.extent.txt"
    # nr1, pt, pl, pr, pb, nr2, dt, nr3, db
    extent_file.write_text("1 20 10 30 40 2 100 3 200\n")
    path_file = tmp_path / "test.path.txt"
    # ppt, dummy, dummy, dummy, dummy, dummy, dummy, dummy, value
    path_file.write_text("0 1 0 0 0 0 0 0 120\n0 2 0 0 0 0 0 0 140\n")
    output_file = tmp_path / "test.box.gmt"

    pre_interpretation.box_elevation(str(extent_file), str(path_file), str(output_file), 2, 10, 0.5, 0.5)

    content = output_file.read_text()
    assert "# @VGMT1.0 @GLINESTRING" in content
    assert "# FEATURE_DATA" in content
    assert "# @Dextent" in content
    assert "# @Dupper_left" in content
    assert "# @Dlower_right" in content
    assert "# @Dground_level" in content
    assert ">\n" in content

def test_all_lines_appends_when_mode_a(tmp_path):
    path_file = tmp_path / "test2.path.txt"
    path_file.write_text("1 2 3 4 120.0 220.0 7 8 9\n")
    output_file = tmp_path / "test2.gmt"
    crs = 4326
    gis = None
    mode = 'w'
    pre_interpretation.all_lines(str(path_file), str(output_file), crs, gis, mode)
    # Append another line
    mode = 'a'
    pre_interpretation.all_lines(str(path_file), str(output_file), crs, gis, mode)
    content = output_file.read_text()
    assert content.count("# @VGMT1.0 @GLINESTRING") == 1  # Only written once
    assert content.count(">") >= 2  # Two features

@pytest.mark.parametrize("depth_lines,line_increments", [(1, 1), (5, 10)])
def test_box_elevation_various_layers(tmp_path, depth_lines, line_increments):
    extent_file = tmp_path / "test3.extent.txt"
    extent_file.write_text("1 20 10 30 40 2 100 3 200\n")
    path_file = tmp_path / "test3.path.txt"
    path_file.write_text("0 1 0 0 0 0 0 0 120\n")
    output_file = tmp_path / "test3.box.gmt"
    pre_interpretation.box_elevation(str(extent_file), str(path_file), str(output_file), depth_lines, line_increments, 0.5, 0.5)
    content = output_file.read_text()
    assert "# @VGMT1.0 @GLINESTRING" in content
    assert "# FEATURE_DATA" in content
    assert content.count(">") >= depth_lines + 3  # 3 boxes + layers

def test_main_prints_bounds(monkeypatch, tmp_path, capsys):
    # Setup fake input/output directories
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    (output_dir / "all_lines").mkdir()

    # Create minimal path and extent files
    (input_dir / "1.path.txt").write_text("1 1 1 1 100.0 200.0 7 8 9\n1 1 4 5 110.0 210.0 8 9 10\n")
    (input_dir / "1.extent.txt").write_text("1 20 10 30 40 2 100 3 200\n")
    # Patch sys.argv
    monkeypatch.setattr('sys.argv', [
        'pre_interpretation.py',
        '-i', str(input_dir),
        '-o', str(output_dir),
        '--crs', '4326',
        '--gis', 'esri_arcmap_0.5',
        '--lines', '2',
        '--lines_increment', '10'
    ])
    # Patch subprocess.run to avoid actually running ogr2ogr
    monkeypatch.setattr(pre_interpretation.subprocess, "run", lambda *a, **k: None)
    # Patch get_ogr_path to return a dummy string
    monkeypatch.setattr(pre_interpretation, "get_ogr_path", lambda: "ogr2ogr")
    # Patch geopandas.read_file to return a dummy GeoDataFrame
    dummy_gdf = gpd.GeoDataFrame({'geometry': []}, geometry='geometry', crs="EPSG:4326")
    monkeypatch.setattr(gpd, "read_file", lambda *a, **k: dummy_gdf)
    # Patch GeoDataFrame.to_crs to just return self
    monkeypatch.setattr(dummy_gdf, "to_crs", lambda *a, **k: dummy_gdf)
    # Patch folium.Map and folium.GeoJson to avoid file IO
    class DummyMap:
        def __init__(self, *a, **k): pass
        def save(self, *a, **k): pass
    class DummyGeoJson:
        def __init__(self, *a, **k): pass
        def add_to(self, m): return self
        def get_bounds(self): return [[0, 0], [1, 1]]
    monkeypatch.setattr(folium, "Map", DummyMap)
    monkeypatch.setattr(folium, "GeoJson", DummyGeoJson)
    # Run main and ensure no exception
    pre_interpretation.main()
    out = capsys.readouterr().out
    assert "bounds are: [[0, 0], [1, 1]]" in out
