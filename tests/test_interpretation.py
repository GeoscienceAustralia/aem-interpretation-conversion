from aemworkflow import interpretation
import sys
import builtins
import io

def test_active_gmt_metadata_to_bdf(tmp_path):
    gmt_content = "@D some metadata\nother line\n@D another metadata\n"
    gmt_file = tmp_path / "test.gmt"
    bdf_file = tmp_path / "test.bdf"
    gmt_file.write_text(gmt_content)

    interpretation.active_gmt_metadata_to_bdf(str(gmt_file), str(bdf_file), "w")
    result = bdf_file.read_text().splitlines()
    assert result == [
        "test.gmt|0|@D some metadata",
        "test.gmt|1|@D another metadata"
    ]

def test_active_shp_to_gmt(monkeypatch):
    called = {}

    def fake_run(cmd, check):
        called['cmd'] = cmd
        called['check'] = check
        return None

    monkeypatch.setattr(interpretation.subprocess, "run", fake_run)
    monkeypatch.setattr(interpretation, "get_ogr_path", lambda: "ogr2ogr")

    interpretation.active_shp_to_gmt("input.shp", "output.gmt")
    assert called['cmd'] == ["ogr2ogr", "-f", "GMT", "output.gmt", "input.shp"]
    assert called['check'] is True

def test_active_extent_control_file(tmp_path):
    extent_file = tmp_path / "extent.txt"
    path_file = tmp_path / "path.txt"
    output_file = tmp_path / "output.gmt"
    out_active_extent = tmp_path / "active_extent.txt"
    extent_file.write_text("123 456 789 012")
    path_file.write_text("LN1 x x x 1.1 2.2\nLN1 x x x 3.3 4.4\nLN2 x x x 5.5 6.6\n")
    crs = "4326"
    gis = None
    mode = "w"

    interpretation.active_extent_control_file(
        str(extent_file), str(path_file),
        str(output_file), str(out_active_extent),
        crs, gis, mode
    )

    out_lines = output_file.read_text().splitlines()
    assert "# @VGMT1.0 @GLINESTRING" == out_lines[0]
    assert out_lines[1].startswith("# @Jp\"")
    assert crs in out_lines[2]
    assert out_lines[2].startswith("# @Jw\"")
    assert "# @Nlinenum" == out_lines[3]
    assert "# @Tinteger" == out_lines[4]
    assert "# FEATURE_DATA" == out_lines[5]
    assert ">" == out_lines[6]
    assert "# @DLN1" == out_lines[7]
    assert "1.1 2.2" == out_lines[8]
    assert "3.3 4.4" == out_lines[9]
    assert ">" == out_lines[10]
    assert "# @DLN2" == out_lines[11]
    assert "5.5 6.6" == out_lines[12]

    assert out_active_extent.read_text().strip() == "123 456 789 012"

def test_main_creates_outputs(monkeypatch, tmp_path):
    # Setup fake input directory and files
    input_dir = tmp_path / "inputs"
    output_dir = tmp_path / "outputs"
    interp_dir = output_dir / "interp"
    all_lines_dir = output_dir / "all_lines"
    input_dir.mkdir()
    interp_dir.mkdir()
    all_lines_dir.mkdir()

    # Create a fake .shp file and corresponding .extent.txt, .path.txt and .gmt files
    shp_file = input_dir / "LN1_interp_001.shp"
    shp_file.touch()
    extent_file = input_dir / "LN1.extent.txt"
    extent_file.write_text("100 200 300 400")
    path_file = input_dir / "LN1.path.txt"
    path_file.touch()
    gmt_file = interp_dir / "LN1_interp.gmt"
    gmt_file.touch()

    # Create a dummy all_lines.geojson for folium
    all_lines_geojson = all_lines_dir / "all_lines.geojson"
    all_lines_geojson.write_text('{"type": "FeatureCollection", "features": []}')

    # Patch sys.argv so argparse doesn't fail
    monkeypatch.setattr('sys.argv', [
        'pre_interpretation.py',
        '-i', str(input_dir),
        '-o', str(output_dir),
    ])

    # Patch get_ogr_path to return a dummy string
    monkeypatch.setattr(interpretation, "get_ogr_path", lambda: "ogr2ogr")

    # Patch subprocess.run to do nothing
    monkeypatch.setattr(interpretation.subprocess, "run", lambda *a, **k: None)

    # Patch geopandas.read_file to return a dummy GeoDataFrame
    class DummyGeoDF:
        crs = "epsg:28349"
        def to_crs(self, epsg=None):
            self.crs = f"epsg:{epsg}"
            return self
        def to_file(self, *a, **k):
            # Write a minimal geojson file for folium
            with open(a[0], "w") as f:
                f.write('{"type": "FeatureCollection", "features": []}')
    monkeypatch.setattr(interpretation.geopandas, "read_file", lambda *a, **k: DummyGeoDF())

    # Patch folium.Map and folium.GeoJson to dummy classes
    class DummyLayer:
        def get_bounds(self): return [[0,0],[1,1]]
        def add_to(self, m): return self
    class DummyMap:
        def __init__(self, *a, **k): self.saved = False
        def save(self, path): self.saved = True
        def add_to(self, m): return self
    monkeypatch.setattr(interpretation.folium, "Map", DummyMap)
    monkeypatch.setattr(interpretation.folium, "GeoJson", lambda *a, **k: DummyLayer())
    monkeypatch.setattr(interpretation.folium, "LayerControl", lambda: DummyLayer())

    # Patch open for folium.GeoJson to read geojson
    orig_open = builtins.open
    def fake_open(file, mode='r', *args, **kwargs):
        if isinstance(file, str) and file.endswith(".geojson"):
            return orig_open(file, mode, *args, **kwargs)
        return orig_open(file, mode, *args, **kwargs)
    monkeypatch.setattr(builtins, "open", fake_open)

    # Patch print to capture output
    output = io.StringIO()
    monkeypatch.setattr(sys, "stderr", output)
    monkeypatch.setattr(sys, "stdout", output)

    # Run main
    interpretation.main()

    # Check that output files were created
    assert (interp_dir / "active_extent.txt").exists()
    assert (interp_dir / "active_path.gmt").exists()
    assert (interp_dir / "met.bdf").exists()
    assert (interp_dir / "active_path.geojson").exists()
    # Check that output contains expected prints
    out = output.getvalue()
    assert "create AEM interp box" in out
    assert "layer interval" in out
    assert "layer count" in out
    assert "completed updating map" in out
