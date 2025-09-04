from pathlib import Path
from aemworkflow import gmt_2_met

def create_test_file(directory, filename, lines):
    file_path = Path(directory) / filename
    with open(file_path, "w") as f:
        f.writelines(lines)
    return file_path

def test_main_prints_expected_lines(tmp_path, capsys):
    # Create two files with suffix 'test'
    lines1 = [
        '"@D"|field2|field3|field4|field5|field6|field7|field8|field9|field10|field11|field12|field13|field14|field15|field16|field17|field18|field19|field20|field21|field22|field23|field24|extra\n',
        'notmatch|field2|field3|field4|field5|field6|field7|field8|field9|field10|field11|field12|field13|field14|field15|field16|field17|field18|field19|field20|field21|field22|field23|field24|extra\n',
        '"@D"|field2|field3|field4|field5|field6|field7|field8|field9|field10|field11|field12|field13|field14|field15|field16|field17|field18|field19|field20|field21|field22|field23|field24|extra\n'
    ]
    lines2 = [
        '"@D"|a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|extra\n'
    ]
    f1 = create_test_file(tmp_path, "file1.test", lines1)
    f2 = create_test_file(tmp_path, "file2.test", lines2)

    # Run main
    gmt_2_met.main(tmp_path, "test")
    out = capsys.readouterr().out

    # Should print 3 lines (2 from file1, 1 from file2)
    assert str(f1) in out
    assert str(f2) in out
    assert out.count(str(f1)) == 2
    assert out.count(str(f2)) == 1
    # Check that fid increments per file
    assert "|0|" in out
    assert "|1|" in out

def test_main_handles_no_matching_files(tmp_path, capsys):
    # No files with the given suffix
    gmt_2_met.main(tmp_path, "doesnotexist")
    out = capsys.readouterr().out
    assert out == ""

def test_main_handles_empty_file(tmp_path, capsys):
    create_test_file(tmp_path, "empty.test", [])
    gmt_2_met.main(tmp_path, "test")
    out = capsys.readouterr().out
    assert out == ""

def test_main_strips_quotes_correctly(tmp_path, capsys):
    lines = [
        '"@D"|\"field2\"|field3|field4|field5|field6|field7|field8|field9|field10|field11|field12|field13|field14|field15|field16|field17|field18|field19|field20|field21|field22|field23|field24|extra\n'
    ]
    create_test_file(tmp_path, "quotes.test", lines)
    gmt_2_met.main(tmp_path, "test")
    out = capsys.readouterr().out
    # Should not have double quotes in output
    assert '"@D"' not in out
    assert '\"field2\"' not in out
    assert 'field2' in out

def test_main_handles_files_with_less_than_24_fields(tmp_path, capsys):
    lines = [
        '"@D"|a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w\n'  # only 24 fields
    ]
    f = create_test_file(tmp_path, "short.test", lines)
    gmt_2_met.main(tmp_path, "test")
    out = capsys.readouterr().out
    # Should print the line, joined by '|'
    assert str(f) in out
    assert out.count('|') >= 25  # filename|fid|24 fields
