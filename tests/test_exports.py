import os
import tempfile
import shutil
import pandas as pd
import pytest
import aemworkflow.exports as exports
from unittest import mock

@pytest.fixture
def temp_sort_dir():
    temp_dir = tempfile.mkdtemp()
    sort_dir = os.path.join(temp_dir, "SORT")
    os.makedirs(sort_dir)
    yield temp_dir, sort_dir
    shutil.rmtree(temp_dir)

def create_prn_file(path, content):
    with open(path, "w") as f:
        f.write(content)

def create_gmtsddd_file(path, header, data):
    with open(path, "w") as f:
        f.write(header)
        f.write(data)

def test_gmtsddd_to_egs(temp_sort_dir):
    temp_dir, sort_dir = temp_sort_dir
    prn_content = "TYPE  OVERAGE  UNDERAGE\nA 1 2\nB 3 4\n"
    prn_path = os.path.join(temp_dir, "features.prn")
    create_prn_file(prn_path, prn_content)

    gmts_content = "# @D0|0|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V\n" \
                   "1 2 3 4 5 6 7 8 9 10\n"
    gmts_path = os.path.join(sort_dir, "100.gmtsddd")
    create_gmtsddd_file(gmts_path, gmts_content[:gmts_content.index('\n')+1], gmts_content[gmts_content.index('\n')+1:])

    exports.gmtsddd_to_egs(temp_dir, prn_path, [100])
    output_path = os.path.join(sort_dir, "output.egs")
    assert os.path.exists(output_path)
    with open(output_path) as f:
        lines = f.readlines()
    assert any("Vertex" in l for l in lines)
    assert any("A" in l for l in lines)

def test_gmtsddd_to_mdc(temp_sort_dir):
    temp_dir, sort_dir = temp_sort_dir
    prn_content = "TYPE  Red  Green  Blue  Other\nA  10  20  30  1\nB 40 50 60 2\n"
    prn_path = os.path.join(temp_dir, "colors.prn")
    create_prn_file(prn_path, prn_content)

    gmts_content = "# @D0|0|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V\n" \
                   "1 2 3 4 5 6 7 8 9 10\n"
    gmts_path = os.path.join(sort_dir, "101.gmtsddd")
    create_gmtsddd_file(gmts_path, gmts_content[:gmts_content.index('\n')+1], gmts_content[gmts_content.index('\n')+1:])

    exports.gmtsddd_to_mdc(temp_dir, prn_path, [101])
    output_path = os.path.join(sort_dir, "output.mdc")
    assert os.path.exists(output_path)
    with open(output_path) as f:
        lines = f.read()
    assert "GOCAD PLine" in lines
    assert "A" in lines

def test_gmtsddd_to_mdch(temp_sort_dir):
    temp_dir, sort_dir = temp_sort_dir
    prn_content = "TYPE  Red  Green  Blue  Other\nA  10  20  30  1\nB 40 50 60 2\n"
    prn_path = os.path.join(temp_dir, "colors.prn")
    create_prn_file(prn_path, prn_content)

    gmts_content = "# @D0|0|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V\n" \
                   "1 2 3 4 5 6 7 8 9 10\n"
    gmts_path = os.path.join(sort_dir, "102.gmtsddd")
    create_gmtsddd_file(gmts_path, gmts_content[:gmts_content.index('\n')+1], gmts_content[gmts_content.index('\n')+1:])

    exports.gmtsddd_to_mdch(temp_dir, prn_path, [102])
    output_path = os.path.join(sort_dir, "output.mdch")
    assert os.path.exists(output_path)
    with open(output_path) as f:
        lines = f.read()
    assert "GOCAD PLine" in lines
    assert "A" in lines

def test_gmts_2_egs(temp_sort_dir):
    temp_dir, sort_dir = temp_sort_dir
    df = pd.DataFrame({
        'TYPE': ['A'],
        'OVERAGE': [10.0],
        'UNDERAGE': [100.0],
        'Blue': [5.0]
    })

    gmts_content = "@D|0|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V\n" \
                   "1 2 3 4 5 6 7 8 9 10\n"
    gmts_path = os.path.join(sort_dir, "103.gmtsddd")
    create_gmtsddd_file(gmts_path, gmts_content[:gmts_content.index('\n')+1], gmts_content[gmts_content.index('\n')+1:])

    with mock.patch("aemworkflow.commands.pd.read_csv", return_value=df):
        exports.gmts_2_egs(temp_dir, 'alt_colors', [103])
        output_path = os.path.join(sort_dir, "103.egs")
        assert os.path.exists(output_path)
        with open(output_path) as f:
            lines = f.read()
        assert "Vertex" in lines
        assert "A" in lines

def test_gmts_2_mdc(temp_sort_dir):
    temp_dir, sort_dir = temp_sort_dir
    prn_content = "Feature classes  Red  Green  Blue\nA  10  20  30\nB  40  50  60\n"
    prn_path = os.path.join(temp_dir, "colors.prn")
    create_prn_file(prn_path, prn_content)

    gmts_content = "@D|0|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V\n" \
                   "1 2 3 4 5 6 7 8 9 10\n"
    gmts_path = os.path.join(sort_dir, "104.gmtsddd")
    create_gmtsddd_file(gmts_path, gmts_content[:gmts_content.index('\n')+1], gmts_content[gmts_content.index('\n')+1:])

    exports.gmts_2_mdc(temp_dir, prn_path, [104])
    output_path = os.path.join(sort_dir, "104.mdc")
    assert os.path.exists(output_path)
    with open(output_path) as f:
        lines = f.read()
    assert "GOCAD PLine" in lines
    assert "A" in lines

def test_main(tmp_path):
    output_directory = tmp_path / "output"
    interp_directory = output_directory / "interp"
    interp_directory.mkdir(parents=True)
    out_active_extent = interp_directory / "active_extent.txt"
    out_active_extent.write_text("123 456 789 012")
    with mock.patch('aemworkflow.exports.gmtsddd_to_egs') as to_egs:
        with mock.patch('aemworkflow.exports.gmtsddd_to_mdc') as to_mdc:
            with mock.patch('aemworkflow.exports.gmtsddd_to_mdch') as to_mdch:
                exports.main('input_dir', str(output_directory), export_mdc=True, export_mdch=False, export_egs=True, boundary='boundary', split='split')
                to_egs.assert_called_once()
                to_mdc.assert_called_once()
                to_mdch.assert_not_called()
