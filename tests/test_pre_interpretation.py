import pytest
from aemworkflow import pre_interpretation

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
