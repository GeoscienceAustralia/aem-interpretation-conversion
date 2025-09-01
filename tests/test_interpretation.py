from aemworkflow import interpretation

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

def test_active_extent_control_file(tmp_path, monkeypatch):
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
