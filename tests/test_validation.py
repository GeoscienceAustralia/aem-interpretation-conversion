import os
import pytest
from aemworkflow import validation
from unittest import mock

class DummyLogger:
    def __init__(self):
        self.messages = []
    def info(self, msg):
        self.messages.append(msg)

@pytest.fixture
def dummy_logger():
    return DummyLogger()

def test_validation_remove_quotes_removes_quotes(tmp_path, dummy_logger):
    input_path = os.path.join(tmp_path, "input.bdf")
    output_path = os.path.join(tmp_path, "output.bdf")
    with open(input_path, "w") as f:
        f.write('abc"def"\n123"456"\n')
    validation.validation_remove_quotes(input_path, output_path, dummy_logger)
    with open(output_path) as f:
        content = f.read()
    assert '"' not in content
    assert content == "abcdef\n123456\n"
    assert "Running remove quotes validation." in dummy_logger.messages
    assert "Completed remove quotes validation." in dummy_logger.messages

def test_validation_qc_units_basic(tmp_path, dummy_logger):
    validation_dir = tmp_path
    os.makedirs(os.path.join(validation_dir, "qc"), exist_ok=True)
    erc_path = os.path.join(validation_dir, "ERC_Stratigraphic_names_Current.txt")
    bdf_2_path = os.path.join(validation_dir, "qc", "met2.bdf")
    # ERC file with 43 fields
    with open(erc_path, "w", encoding="utf-8") as f:
        f.write("|".join(["unit1", "num1"] + ["x"]*41) + "\n")
    # Interp file with matching and non-matching units
    with open(bdf_2_path, "w") as f:
        # fields[7]=unit1, fields[8]=num1 (match)
        fields = [""]*25
        fields[7] = "unit1"
        fields[8] = "num1"
        f.write("|".join(fields) + "\n")
        # fields[7]=unit2, fields[8]=num2 (no match)
        fields[7] = "unit2"
        fields[8] = "num2"
        f.write("|".join(fields) + "\n")
    validation.validation_qc_units(erc_path, bdf_2_path, validation_dir, dummy_logger)
    summary_files = [f for f in os.listdir(os.path.join(validation_dir, "qc")) if f.startswith("AEM_validation_summary_")]
    assert summary_files, "Summary file not created"
    with open(os.path.join(validation_dir, "qc", summary_files[0])) as f:
        lines = f.readlines()
    assert any("matched,unit1,num1,1" in line for line in lines)
    assert any("no match,unit2,num2,1" in line for line in lines)
    assert "Running qc_units validation." in dummy_logger.messages
    assert "completed qc_units validation." in dummy_logger.messages

def test_validation_qc_units_short_nf(tmp_path, dummy_logger):
    validation_dir = tmp_path
    os.makedirs(os.path.join(validation_dir, "qc"), exist_ok=True)
    erc_path = os.path.join(validation_dir, "ERC_Stratigraphic_names_Current.txt")
    bdf_2_path = os.path.join(validation_dir, "qc", "met2.bdf")
    with open(erc_path, "w", encoding="utf-8") as f:
        f.write("|".join(["unit1", "num1"] + ["x"]*40) + "\n")
    # Write a line with less than 25 fields
    with open(bdf_2_path, "w") as f:
        f.write("a|b|c|d|e|f|g|||j|||m||\n")
    validation.validation_qc_units(erc_path, bdf_2_path, validation_dir, dummy_logger)
    short_nf_path = os.path.join(validation_dir, "qc", "short_nf.log")
    assert os.path.exists(short_nf_path)
    nf_path = "asud_nf.asc"
    assert os.path.exists(nf_path)
    with open(short_nf_path) as f:
        content = f.read()
    assert "15 a b" in content

def test_validation_main_removes_quotes_and_validates(tmp_path):
    input_dir = tmp_path
    output_dir = tmp_path
    erc_path = os.path.join(input_dir, "test.asud")
    bdf_path = os.path.join(output_dir, "interp", "met.bdf")
    ap = mock.MagicMock()
    ap.add_argument = mock.MagicMock()
    ap.parse_args = mock.MagicMock(return_value=mock.MagicMock(
        input_directory=str(input_dir),
        output_directory=str(output_dir),
        asud='test.asud'
    ))
    with mock.patch('argparse.ArgumentParser', return_value=ap):
        with mock.patch('aemworkflow.validation.validation_remove_quotes') as remove_quotes:
            with mock.patch('aemworkflow.validation.validation_qc_units') as qc_units:
                validation.main()
                remove_quotes.assert_called_once_with(bdf_path, os.path.join(output_dir, "qc", "met2.bdf"))
                qc_units.assert_called_once_with(erc_path, os.path.join(output_dir, "qc", "met2.bdf"), str(output_dir))
