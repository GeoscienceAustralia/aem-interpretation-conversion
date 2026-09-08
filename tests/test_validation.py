import os
from datetime import date
from unittest import mock

import pytest

from aemworkflow import validation


class DummyLogger:
    def __init__(self):
        self.messages = []

    def info(self, msg):
        self.messages.append(msg)

    def warning(self, msg):
        self.messages.append(msg)

    def error(self, msg):
        self.messages.append(msg)


@pytest.fixture
def dummy_logger():
    return DummyLogger()


def _write_lookup_file(path, values):
    with open(path, "w", encoding="utf-8") as lookup_file:
        lookup_file.write("value description\n")

        for value in values:
            lookup_file.write(f"{value} description\n")


def _create_bdf_fields():
    fields = [""] * 26
    fields[0] = "5001001_interp.gmt"
    fields[1] = "1"
    fields[2] = "# @D0"
    fields[3] = "BASE_Cenozoic_TOP_Paleozoic"
    fields[4] = "H"
    fields[5] = "unc"
    fields[6] = "IAEM"
    fields[7] = "unit1"
    fields[8] = "num1"
    fields[9] = "H"
    fields[10] = "unit2"
    fields[11] = "num2"
    fields[12] = "M"
    fields[13] = "unit3"
    fields[14] = "num3"
    fields[15] = "L"
    fields[24] = "TEST"
    fields[25] = "11/08/2026"
    return fields


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

    with open(erc_path, "w", encoding="utf-8") as f:
        f.write("|".join(["unit1", "num1"] + ["x"] * 41) + "\n")

    with open(bdf_2_path, "w") as f:
        fields = [""] * 26
        fields[7] = "unit1"
        fields[8] = "num1"
        f.write("|".join(fields) + "\n")

        fields = [""] * 26
        fields[7] = "unit2"
        fields[8] = "num2"
        f.write("|".join(fields) + "\n")

    validation.validation_qc_units(erc_path, bdf_2_path, validation_dir, dummy_logger)

    summary_files = [f for f in os.listdir(os.path.join(validation_dir, "qc")) if f.startswith("ASUD_validation_sum")]

    assert summary_files, "Summary file not created"

    with open(os.path.join(validation_dir, "qc", summary_files[0])) as f:
        lines = f.readlines()

    assert any("matched,unit1,num1,1" in line for line in lines)
    assert any("no match,unit2,num2,1" in line for line in lines)
    assert "Running qc_units validation." in dummy_logger.messages
    assert "completed qc_units validation." in dummy_logger.messages


def test_validation_qc_units_csv_format(tmp_path, dummy_logger):
    validation_dir = tmp_path
    os.makedirs(os.path.join(validation_dir, "qc"), exist_ok=True)
    erc_path = os.path.join(validation_dir, "ERC_Stratigraphic_names_Current.csv")
    bdf_2_path = os.path.join(validation_dir, "qc", "met2.bdf")

    with open(erc_path, "w", encoding="utf-8", newline="") as f:
        f.write("STRATIGRAPHIC NAME,STRAT NO\n")
        f.write("unit1,num1\n")

    with open(bdf_2_path, "w") as f:
        fields = [""] * 26
        fields[7] = "unit1"
        fields[8] = "num1"
        f.write("|".join(fields) + "\n")

        fields = [""] * 26
        fields[7] = "unit2"
        fields[8] = "num2"
        f.write("|".join(fields) + "\n")

    validation.validation_qc_units(erc_path, bdf_2_path, validation_dir, dummy_logger)

    summary_files = [f for f in os.listdir(os.path.join(validation_dir, "qc")) if f.startswith("ASUD_validation_sum")]

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
        f.write("|".join(["unit1", "num1"] + ["x"] * 40) + "\n")
    # Write a line with less than 25 fields
    with open(bdf_2_path, "w") as f:
        f.write("a|b|c|d|e|f|g|||j|||m||\n")
    validation.validation_qc_units(erc_path, bdf_2_path, validation_dir, dummy_logger)
    short_nf_path = os.path.join(validation_dir, "qc", "short_nf.log")
    assert os.path.exists(short_nf_path)
    with open(short_nf_path) as f:
        content = f.read()
    assert "15 a b" in content


def test_initialise_error_log_writes_header(tmp_path):
    qc_dir = tmp_path / "qc"
    qc_dir.mkdir()

    validation.initialise_error_log(qc_dir)

    error_log_path = qc_dir / "error_list.log"
    content = error_log_path.read_text(encoding="utf-8")

    assert content == "|".join(validation.ERROR_LOG_HEADER) + "\n"
    assert content.startswith("ERROR_GENERAL|ERROR_TYPE|ERROR_FIELD1|ERROR_FIELD1_ENTRY|ERROR_FIELD2|" 
    "ERROR_FIELD2_ENTRY|ERROR_COUNT|")
    assert "|FLIGHT_LINE|SHAPEFILE_FID|Type|BoundConf|" in content


def test_load_lookup_values(tmp_path):
    lookup_path = tmp_path / "lookup.txt"
    _write_lookup_file(lookup_path, ["H", "M", "L"])

    result = validation._load_lookup_values(lookup_path)

    assert result == {"H", "M", "L"}


def test_load_lookup_values_empty_file_raises_error(tmp_path):
    lookup_path = tmp_path / "lookup.txt"
    lookup_path.write_text("value description\n", encoding="utf-8")

    with pytest.raises(ValueError, match="No values found in lookup file"):
        validation._load_lookup_values(lookup_path)


def test_write_validation_error_aligns_fields(tmp_path):
    error_log_path = tmp_path / "error_list.log"
    fields = _create_bdf_fields()

    with open(error_log_path, "w", encoding="utf-8") as error_list_file:
        validation._write_validation_error(error_list_file, "confidence", "no match", "BoundConf", "X", "N/A", "N/A",
                                           fields)

    line = error_log_path.read_text(encoding="utf-8").strip()
    output_fields = line.split("|")

    assert output_fields[:7] == ["confidence", "no match", "BoundConf", "X", "N/A", "N/A", ""]
    assert len(output_fields) == 32


def test_write_validation_error_pads_short_bdf_records(tmp_path):
    error_log_path = tmp_path / "error_list.log"
    fields = ["flight", "1", "# @D0"]

    with open(error_log_path, "w", encoding="utf-8") as error_list_file:
        validation._write_validation_error(error_list_file, "bdf", "incorrect field count", "BDFFieldCount", "3", "N/A",
                                            "N/A", fields)

    output_fields = error_log_path.read_text(encoding="utf-8").strip().split("|")

    assert output_fields[:7] == ['bdf', 'incorrect field count', 'BDFFieldCount', '3', 'N/A', 'N/A', '']
    assert output_fields[7] == 'flight'
    assert output_fields[8] == '1'
    assert output_fields[9] == ''
    assert len(output_fields) == 32


def test_validation_mandatory_fields_invalid_confidence_is_no_match(tmp_path, dummy_logger):
    qc_dir = tmp_path / "qc"
    qc_dir.mkdir()

    confidence_lookup = tmp_path / "LU_CONFIDENCE.txt"
    contact_lookup = tmp_path / "LU_CONTACT_TYPES.txt"
    interp_lookup = tmp_path / "LU_INTERP_BASIS.txt"
    bdf_path = qc_dir / "met2.bdf"

    _write_lookup_file(confidence_lookup, ["H", "M", "L"])
    _write_lookup_file(contact_lookup, ["unc", "con", "flt"])
    _write_lookup_file(interp_lookup, ["IAEM", "GIOG", "RGI"])

    fields = _create_bdf_fields()
    fields[4] = "X"
    bdf_path.write_text("|".join(fields) + "\n", encoding="utf-8")

    validation.initialise_error_log(qc_dir)
    validation.validation_mandatory_fields(confidence_lookup, contact_lookup, interp_lookup, bdf_path, tmp_path,
                                           dummy_logger)

    d = date.today().strftime("%Y%m%d")
    confidence_summary = (qc_dir / f"Confidence_validation_summary_{d}.txt").read_text(encoding="utf-8")
    error_log = (qc_dir / "error_list.log").read_text(encoding="utf-8")

    assert "no match,BoundConf,X,1" in confidence_summary
    assert "confidence|no match|BoundConf|X|N/A|N/A|" in error_log


def test_validation_mandatory_fields_blank_confidence_allowed(tmp_path, dummy_logger):
    qc_dir = tmp_path / "qc"
    qc_dir.mkdir()

    confidence_lookup = tmp_path / "LU_CONFIDENCE.txt"
    contact_lookup = tmp_path / "LU_CONTACT_TYPES.txt"
    interp_lookup = tmp_path / "LU_INTERP_BASIS.txt"
    bdf_path = qc_dir / "met2.bdf"

    _write_lookup_file(confidence_lookup, ["H", "M", "L"])
    _write_lookup_file(contact_lookup, ["unc"])
    _write_lookup_file(interp_lookup, ["IAEM"])

    fields = _create_bdf_fields()
    fields[7] = ""
    fields[8] = ""
    fields[9] = ""
    fields[10] = ""
    fields[11] = ""
    fields[12] = ""
    fields[13] = ""
    fields[14] = ""
    fields[15] = ""
    bdf_path.write_text("|".join(fields) + "\n", encoding="utf-8")

    validation.initialise_error_log(qc_dir)
    validation.validation_mandatory_fields(confidence_lookup, contact_lookup, interp_lookup, bdf_path, tmp_path,
                                           dummy_logger)

    d = date.today().strftime("%Y%m%d")
    confidence_summary = (qc_dir / f"Confidence_validation_summary_{d}.txt").read_text(encoding="utf-8")

    assert "blank allowed,OvrConf,,1" in confidence_summary
    assert "blank allowed,UndConf,,1" in confidence_summary
    assert "blank allowed,WithinConf,,1" in confidence_summary


def test_validation_mandatory_fields_missing_related_confidence(tmp_path, dummy_logger):
    qc_dir = tmp_path / "qc"
    qc_dir.mkdir()

    confidence_lookup = tmp_path / "LU_CONFIDENCE.txt"
    contact_lookup = tmp_path / "LU_CONTACT_TYPES.txt"
    interp_lookup = tmp_path / "LU_INTERP_BASIS.txt"
    bdf_path = qc_dir / "met2.bdf"

    _write_lookup_file(confidence_lookup, ["H", "M", "L"])
    _write_lookup_file(contact_lookup, ["unc"])
    _write_lookup_file(interp_lookup, ["IAEM"])

    fields = _create_bdf_fields()
    fields[7] = "unit1"
    fields[9] = ""
    bdf_path.write_text("|".join(fields) + "\n", encoding="utf-8")

    validation.initialise_error_log(qc_dir)
    validation.validation_mandatory_fields(confidence_lookup, contact_lookup, interp_lookup, bdf_path, tmp_path,
                                           dummy_logger)

    d = date.today().strftime("%Y%m%d")
    confidence_summary = (qc_dir / f"Confidence_validation_summary_{d}.txt").read_text(encoding="utf-8")
    error_log = (qc_dir / "error_list.log").read_text(encoding="utf-8")

    assert "missing,OvrConf,,1" in confidence_summary
    assert "confidence|missing|OvrConf|<blank>|N/A|N/A|" in error_log


def test_validation_mandatory_fields_invalid_contact_type(tmp_path, dummy_logger):
    qc_dir = tmp_path / "qc"
    qc_dir.mkdir()

    confidence_lookup = tmp_path / "LU_CONFIDENCE.txt"
    contact_lookup = tmp_path / "LU_CONTACT_TYPES.txt"
    interp_lookup = tmp_path / "LU_INTERP_BASIS.txt"
    bdf_path = qc_dir / "met2.bdf"

    _write_lookup_file(confidence_lookup, ["H", "M", "L"])
    _write_lookup_file(contact_lookup, ["unc", "con", "flt", "unk"])
    _write_lookup_file(interp_lookup, ["IAEM"])

    fields = _create_bdf_fields()
    fields[5] = "ukn"
    bdf_path.write_text("|".join(fields) + "\n", encoding="utf-8")

    validation.initialise_error_log(qc_dir)
    validation.validation_mandatory_fields(confidence_lookup, contact_lookup, interp_lookup, bdf_path, tmp_path,
                                           dummy_logger)

    d = date.today().strftime("%Y%m%d")
    contact_summary = (qc_dir / f"Contact_type_validation_summary_{d}.txt").read_text(encoding="utf-8")
    error_log = (qc_dir / "error_list.log").read_text(encoding="utf-8")

    assert "no match,ContactTyp,ukn,1" in contact_summary
    assert "contact type|no match|ContactTyp|ukn|N/A|N/A|" in error_log


def test_validation_mandatory_fields_multiple_interpretation_basis_values(tmp_path, dummy_logger):
    qc_dir = tmp_path / "qc"
    qc_dir.mkdir()

    confidence_lookup = tmp_path / "LU_CONFIDENCE.txt"
    contact_lookup = tmp_path / "LU_CONTACT_TYPES.txt"
    interp_lookup = tmp_path / "LU_INTERP_BASIS.txt"
    bdf_path = qc_dir / "met2.bdf"

    _write_lookup_file(confidence_lookup, ["H", "M", "L"])
    _write_lookup_file(contact_lookup, ["unc"])
    _write_lookup_file(interp_lookup, ["IAEM", "GIOG"])

    fields = _create_bdf_fields()
    fields[6] = "IAEM;AEM"
    bdf_path.write_text("|".join(fields) + "\n", encoding="utf-8")

    validation.initialise_error_log(qc_dir)
    validation.validation_mandatory_fields(confidence_lookup, contact_lookup, interp_lookup, bdf_path, tmp_path,
                                           dummy_logger)

    d = date.today().strftime("%Y%m%d")
    interp_summary = (qc_dir / f"Interpretation_basis_validation_summary_{d}.txt").read_text(encoding="utf-8")
    error_log = (qc_dir / "error_list.log").read_text(encoding="utf-8")

    assert "matched,BasisOfInt,IAEM,1" in interp_summary
    assert "no match,BasisOfInt,AEM,1" in interp_summary
    assert "interpretation basis|no match|BasisOfInt|AEM|N/A|N/A|" in error_log


def test_validation_mandatory_fields_detects_comma_and_field_name(tmp_path, dummy_logger):
    qc_dir = tmp_path / "qc"
    qc_dir.mkdir()

    confidence_lookup = tmp_path / "LU_CONFIDENCE.txt"
    contact_lookup = tmp_path / "LU_CONTACT_TYPES.txt"
    interp_lookup = tmp_path / "LU_INTERP_BASIS.txt"
    bdf_path = qc_dir / "met2.bdf"

    _write_lookup_file(confidence_lookup, ["H", "M", "L"])
    _write_lookup_file(contact_lookup, ["unc"])
    _write_lookup_file(interp_lookup, ["IAEM"])

    fields = _create_bdf_fields()
    fields[21] = "This comment, contains a comma"
    bdf_path.write_text("|".join(fields) + "\n", encoding="utf-8")

    validation.initialise_error_log(qc_dir)
    validation.validation_mandatory_fields(confidence_lookup, contact_lookup, interp_lookup, bdf_path, tmp_path,
                                           dummy_logger)

    d = date.today().strftime("%Y%m%d")
    comma_summary = (qc_dir / f"Comma_validation_summary_{d}.txt").read_text(encoding="utf-8")
    error_log = (qc_dir / "error_list.log").read_text(encoding="utf-8")

    assert 'comma found,Comment,"This comment, contains a comma",1' in comma_summary
    assert "comma|comma found|Comment|This comment, contains a comma|N/A|N/A|" in error_log


def test_validation_mandatory_fields_missing_contact_and_basis(tmp_path, dummy_logger):
    qc_dir = tmp_path / "qc"
    qc_dir.mkdir()

    confidence_lookup = tmp_path / "LU_CONFIDENCE.txt"
    contact_lookup = tmp_path / "LU_CONTACT_TYPES.txt"
    interp_lookup = tmp_path / "LU_INTERP_BASIS.txt"
    bdf_path = qc_dir / "met2.bdf"

    _write_lookup_file(confidence_lookup, ["H", "M", "L"])
    _write_lookup_file(contact_lookup, ["unc"])
    _write_lookup_file(interp_lookup, ["IAEM"])

    fields = _create_bdf_fields()
    fields[5] = ""
    fields[6] = ""
    bdf_path.write_text("|".join(fields) + "\n", encoding="utf-8")

    validation.initialise_error_log(qc_dir)
    validation.validation_mandatory_fields(confidence_lookup, contact_lookup, interp_lookup, bdf_path, tmp_path,
                                           dummy_logger)

    d = date.today().strftime("%Y%m%d")
    contact_summary = (qc_dir / f"Contact_type_validation_summary_{d}.txt").read_text(encoding="utf-8")
    interp_summary = (qc_dir / f"Interpretation_basis_validation_summary_{d}.txt").read_text(encoding="utf-8")

    assert "missing,ContactTyp,,1" in contact_summary
    assert "missing,BasisOfInt,,1" in interp_summary


def test_validation_mandatory_fields_malformed_record(tmp_path, dummy_logger):
    qc_dir = tmp_path / "qc"
    qc_dir.mkdir()

    confidence_lookup = tmp_path / "LU_CONFIDENCE.txt"
    contact_lookup = tmp_path / "LU_CONTACT_TYPES.txt"
    interp_lookup = tmp_path / "LU_INTERP_BASIS.txt"
    bdf_path = qc_dir / "met2.bdf"

    _write_lookup_file(confidence_lookup, ["H"])
    _write_lookup_file(contact_lookup, ["unc"])
    _write_lookup_file(interp_lookup, ["IAEM"])

    bdf_path.write_text("flight|1|# @D0\n", encoding="utf-8")

    validation.initialise_error_log(qc_dir)
    validation.validation_mandatory_fields(confidence_lookup, contact_lookup, interp_lookup, bdf_path, tmp_path,
                                           dummy_logger)

    error_log = (qc_dir / "error_list.log").read_text(encoding="utf-8")

    assert "bdf|incorrect field count|BDFFieldCount|3|N/A|N/A|" in error_log
    assert "Found 1 malformed BDF records." in dummy_logger.messages


def test_validation_main_removes_quotes_and_validates(tmp_path):
    input_dir = str(tmp_path)
    output_dir = str(tmp_path)

    erc_path = os.path.join(input_dir, "test.asud")
    confidence_path = os.path.join(input_dir, "LU_CONFIDENCE.txt")
    contact_path = os.path.join(input_dir, "LU_CONTACT_TYPES.txt")
    interp_path = os.path.join(input_dir, "LU_INTERP_BASIS.txt")
    bdf_path = os.path.join(output_dir, "interp", "met.bdf")
    bdf_out_path = os.path.join(output_dir, "qc", "met2.bdf")
    qc_output_dir = os.path.join(output_dir, "qc")

    with mock.patch("aemworkflow.validation.validation_remove_quotes") as remove_quotes:
        with mock.patch("aemworkflow.validation.initialise_error_log") as initialise_error_log:
            with mock.patch("aemworkflow.validation.validation_qc_units") as qc_units:
                with mock.patch("aemworkflow.validation.validation_mandatory_fields") as mandatory_fields:
                    with mock.patch("aemworkflow.validation.finalise_error_log"):
                        validation.main(input_dir, output_dir, "test.asud", "LU_CONFIDENCE.txt", "LU_CONTACT_TYPES.txt",
                                        "LU_INTERP_BASIS.txt")

    remove_quotes.assert_called_once_with(bdf_path, bdf_out_path)
    initialise_error_log.assert_called_once_with(qc_output_dir)
    qc_units.assert_called_once_with(erc_path, bdf_out_path, output_dir)
    mandatory_fields.assert_called_once_with(confidence_path, contact_path, interp_path, bdf_out_path, output_dir)


def test_finalise_error_log_adds_error_counts(tmp_path):
    error_log_path = tmp_path / 'error_list.log'

    error_log_path.write_text(
        'ERROR_GENERAL|ERROR_TYPE|ERROR_FIELD1|ERROR_FIELD1_ENTRY|ERROR_FIELD2|ERROR_FIELD2_ENTRY|ERROR_COUNT|'
        'FLIGHT_LINE|SHAPEFILE_FID|Type\n'
        'confidence|missing|BoundConf|<blank>|N/A|N/A||5001001_interp.gmt|10|Major_fault\n'
        'contact type|missing|ContactTyp|<blank>|N/A|N/A||5001001_interp.gmt|10|Major_fault\n'
        'interpretation basis|missing|BasisOfInt|<blank>|N/A|N/A||5001001_interp.gmt|10|Major_fault\n'
        'confidence|no match|BoundConf|X|N/A|N/A||5001001_interp.gmt|11|Major_fault\n',
        encoding='utf-8'
    )

    validation.finalise_error_log(tmp_path)

    lines = error_log_path.read_text(encoding='utf-8').splitlines()

    assert lines[0].startswith('ERROR_GENERAL|ERROR_TYPE|ERROR_FIELD1')
    assert lines[1].split('|')[6] == '3'
    assert lines[2].split('|')[6] == '3'
    assert lines[3].split('|')[6] == '3'
    assert lines[4].split('|')[6] == '1'


def test_finalise_error_log_counts_by_flight_line_and_fid(tmp_path):
    error_log_path = tmp_path / 'error_list.log'

    error_log_path.write_text(
        'ERROR_GENERAL|ERROR_TYPE|ERROR_FIELD1|ERROR_FIELD1_ENTRY|ERROR_FIELD2|ERROR_FIELD2_ENTRY|ERROR_COUNT|'
        'FLIGHT_LINE|SHAPEFILE_FID|Type\n'
        'confidence|missing|BoundConf|<blank>|N/A|N/A||5001001_interp.gmt|10|Major_fault\n'
        'contact type|missing|ContactTyp|<blank>|N/A|N/A||5001001_interp.gmt|10|Major_fault\n'
        'confidence|missing|BoundConf|<blank>|N/A|N/A||5002001_interp.gmt|10|Major_fault\n',
        encoding='utf-8'
    )

    validation.finalise_error_log(tmp_path)

    rows = [
        line.split('|')
        for line in error_log_path.read_text(encoding='utf-8').splitlines()[1:]
    ]

    assert rows[0][6] == '2'
    assert rows[1][6] == '2'
    assert rows[2][6] == '1'


def _write_era_lookup_file(path, rows):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write('STRATIGRAPHIC NAME,STRAT NO\n')
        for name, no in rows:
            f.write(f'{name},{no}\n')


def _make_bdf_record(type_value, over_name='', over_no='', under_name='', under_no='', within_name='', within_no=''):
    fields = [''] * 26
    fields[0] = '5001001_interp.gmt'
    fields[1] = '1'
    fields[2] = '# @D0'
    fields[3] = type_value
    fields[4] = 'H'
    fields[5] = 'unc'
    fields[6] = 'IAEM'
    fields[7] = over_name
    fields[8] = over_no
    fields[9] = 'H'
    fields[10] = under_name
    fields[11] = under_no
    fields[12] = 'M'
    fields[13] = within_name
    fields[14] = within_no
    fields[15] = 'L'
    fields[24] = 'TEST'
    fields[25] = '11/08/2026'
    return '|'.join(fields)


def test_validation_asud_eras_matched_base_top(tmp_path, dummy_logger):
    qc_dir = tmp_path / 'qc'
    qc_dir.mkdir()
    bdf_path = qc_dir / 'met2.bdf'
    cenozoic_path = tmp_path / 'cenozoic.csv'
    paleozoic_path = tmp_path / 'paleozoic.csv'

    _write_era_lookup_file(cenozoic_path, [('UnitA', 'N001')])
    _write_era_lookup_file(paleozoic_path, [('UnitB', 'N002')])

    bdf_path.write_text(
        _make_bdf_record('BASE_Cenozoic_TOP_Paleozoic', over_name='UnitA', over_no='N001',
                         under_name='UnitB', under_no='N002') + '\n',
        encoding='utf-8'
    )

    validation.initialise_error_log(qc_dir)
    validation.validation_asud_eras(bdf_path, tmp_path,
                                    {'Cenozoic': cenozoic_path, 'Paleozoic': paleozoic_path},
                                    dummy_logger)

    d = date.today().strftime('%Y%m%d')
    summary = (qc_dir / f'ASUD_age_validation_summary_{d}.txt').read_text(encoding='utf-8')

    assert 'matched,Cenozoic,Cenozoic,OvrStrtUnt,OvrStratNo,UnitA,N001,1' in summary
    assert 'matched,Paleozoic,Paleozoic,UndStrtUnt,UndStratNo,UnitB,N002,1' in summary
    assert 'Running ASUD geological Era validation.' in dummy_logger.messages
    assert any('Records checked: 1' in msg for msg in dummy_logger.messages)


def test_validation_asud_eras_age_mismatch_over(tmp_path, dummy_logger):
    qc_dir = tmp_path / 'qc'
    qc_dir.mkdir()
    bdf_path = qc_dir / 'met2.bdf'
    cenozoic_path = tmp_path / 'cenozoic.csv'
    paleozoic_path = tmp_path / 'paleozoic.csv'

    _write_era_lookup_file(cenozoic_path, [('UnitA', 'N001')])
    _write_era_lookup_file(paleozoic_path, [('UnitB', 'N002')])

    # Type says BASE_Mesozoic_TOP_Paleozoic but UnitA is Cenozoic
    bdf_path.write_text(
        _make_bdf_record('BASE_Mesozoic_TOP_Paleozoic', over_name='UnitA', over_no='N001',
                         under_name='UnitB', under_no='N002') + '\n',
        encoding='utf-8'
    )

    validation.initialise_error_log(qc_dir)
    validation.validation_asud_eras(bdf_path, tmp_path,
                                    {'Cenozoic': cenozoic_path, 'Paleozoic': paleozoic_path},
                                    dummy_logger)

    d = date.today().strftime('%Y%m%d')
    summary = (qc_dir / f'ASUD_age_validation_summary_{d}.txt').read_text(encoding='utf-8')
    error_log = (qc_dir / 'error_list.log').read_text(encoding='utf-8')

    assert 'age mismatch,Mesozoic,Cenozoic,OvrStrtUnt,OvrStratNo,UnitA,N001,1' in summary
    assert 'over|age mismatch - interpreted: Mesozoic, ASUD: Cenozoic|OvrStrtUnt|UnitA|OvrStratNo|N001|' in error_log


def test_validation_asud_eras_age_mismatch_under(tmp_path, dummy_logger):
    qc_dir = tmp_path / 'qc'
    qc_dir.mkdir()
    bdf_path = qc_dir / 'met2.bdf'
    cenozoic_path = tmp_path / 'cenozoic.csv'
    paleozoic_path = tmp_path / 'paleozoic.csv'

    _write_era_lookup_file(cenozoic_path, [('UnitA', 'N001')])
    _write_era_lookup_file(paleozoic_path, [('UnitB', 'N002')])

    # Type says BASE_Cenozoic_TOP_Mesozoic but UnitB is Paleozoic
    bdf_path.write_text(
        _make_bdf_record('BASE_Cenozoic_TOP_Mesozoic', over_name='UnitA', over_no='N001',
                         under_name='UnitB', under_no='N002') + '\n',
        encoding='utf-8'
    )

    validation.initialise_error_log(qc_dir)
    validation.validation_asud_eras(bdf_path, tmp_path,
                                    {'Cenozoic': cenozoic_path, 'Paleozoic': paleozoic_path},
                                    dummy_logger)

    d = date.today().strftime('%Y%m%d')
    summary = (qc_dir / f'ASUD_age_validation_summary_{d}.txt').read_text(encoding='utf-8')
    error_log = (qc_dir / 'error_list.log').read_text(encoding='utf-8')

    assert 'age mismatch,Mesozoic,Paleozoic,UndStrtUnt,UndStratNo,UnitB,N002,1' in summary
    assert 'under|age mismatch - interpreted: Mesozoic, ASUD: Paleozoic|UndStrtUnt|UnitB|UndStratNo|N002|' in error_log


def test_validation_asud_eras_matched_within(tmp_path, dummy_logger):
    qc_dir = tmp_path / 'qc'
    qc_dir.mkdir()
    bdf_path = qc_dir / 'met2.bdf'
    cenozoic_path = tmp_path / 'cenozoic.csv'

    _write_era_lookup_file(cenozoic_path, [('UnitC', 'N003')])

    bdf_path.write_text(
        _make_bdf_record('WITHIN_Cenozoic', within_name='UnitC', within_no='N003') + '\n',
        encoding='utf-8'
    )

    validation.initialise_error_log(qc_dir)
    validation.validation_asud_eras(bdf_path, tmp_path, {'Cenozoic': cenozoic_path}, dummy_logger)

    d = date.today().strftime('%Y%m%d')
    summary = (qc_dir / f'ASUD_age_validation_summary_{d}.txt').read_text(encoding='utf-8')

    assert 'matched,Cenozoic,Cenozoic,WithinStrt,WithinStNo,UnitC,N003,1' in summary


def test_validation_asud_eras_age_mismatch_within(tmp_path, dummy_logger):
    qc_dir = tmp_path / 'qc'
    qc_dir.mkdir()
    bdf_path = qc_dir / 'met2.bdf'
    cenozoic_path = tmp_path / 'cenozoic.csv'

    _write_era_lookup_file(cenozoic_path, [('UnitC', 'N003')])

    # Type says WITHIN_Paleozoic but UnitC is Cenozoic
    bdf_path.write_text(
        _make_bdf_record('WITHIN_Paleozoic', within_name='UnitC', within_no='N003') + '\n',
        encoding='utf-8'
    )

    validation.initialise_error_log(qc_dir)
    validation.validation_asud_eras(bdf_path, tmp_path, {'Cenozoic': cenozoic_path}, dummy_logger)

    d = date.today().strftime('%Y%m%d')
    summary = (qc_dir / f'ASUD_age_validation_summary_{d}.txt').read_text(encoding='utf-8')
    error_log = (qc_dir / 'error_list.log').read_text(encoding='utf-8')

    assert 'age mismatch,Paleozoic,Cenozoic,WithinStrt,WithinStNo,UnitC,N003,1' in summary
    assert 'within|age mismatch - interpreted: Paleozoic, ASUD: Cenozoic|WithinStrt|UnitC|WithinStNo|N003|' in error_log


def test_validation_asud_eras_skips_unit_not_in_asud(tmp_path, dummy_logger):
    qc_dir = tmp_path / 'qc'
    qc_dir.mkdir()
    bdf_path = qc_dir / 'met2.bdf'
    cenozoic_path = tmp_path / 'cenozoic.csv'

    _write_era_lookup_file(cenozoic_path, [('KnownUnit', 'K001')])

    # UnitX/N999 not in any era lookup — should be skipped silently
    bdf_path.write_text(
        _make_bdf_record('BASE_Cenozoic_TOP_Paleozoic', over_name='UnitX', over_no='N999',
                         under_name='UnitY', under_no='N888') + '\n',
        encoding='utf-8'
    )

    validation.initialise_error_log(qc_dir)
    validation.validation_asud_eras(bdf_path, tmp_path, {'Cenozoic': cenozoic_path}, dummy_logger)

    d = date.today().strftime('%Y%m%d')
    summary = (qc_dir / f'ASUD_age_validation_summary_{d}.txt').read_text(encoding='utf-8')
    error_log = (qc_dir / 'error_list.log').read_text(encoding='utf-8')

    assert summary.strip() == 'result,interpretation value,ASUD value,field 1,field 2,strat unit,strat no,count'
    assert 'age mismatch' not in error_log


def test_validation_asud_eras_skips_blank_strat_fields(tmp_path, dummy_logger):
    qc_dir = tmp_path / 'qc'
    qc_dir.mkdir()
    bdf_path = qc_dir / 'met2.bdf'
    cenozoic_path = tmp_path / 'cenozoic.csv'

    _write_era_lookup_file(cenozoic_path, [('UnitA', 'N001')])

    # over fields are blank — should be skipped
    bdf_path.write_text(
        _make_bdf_record('BASE_Cenozoic_TOP_Paleozoic', over_name='', over_no='') + '\n',
        encoding='utf-8'
    )

    validation.initialise_error_log(qc_dir)
    validation.validation_asud_eras(bdf_path, tmp_path, {'Cenozoic': cenozoic_path}, dummy_logger)

    d = date.today().strftime('%Y%m%d')
    summary = (qc_dir / f'ASUD_age_validation_summary_{d}.txt').read_text(encoding='utf-8')

    assert summary.strip() == 'result,interpretation value,ASUD value,field 1,field 2,strat unit,strat no,count'


def test_validation_asud_eras_malformed_record(tmp_path, dummy_logger):
    qc_dir = tmp_path / 'qc'
    qc_dir.mkdir()
    bdf_path = qc_dir / 'met2.bdf'
    cenozoic_path = tmp_path / 'cenozoic.csv'

    _write_era_lookup_file(cenozoic_path, [('UnitA', 'N001')])

    bdf_path.write_text('flight|1|# @D0\n', encoding='utf-8')

    validation.initialise_error_log(qc_dir)
    validation.validation_asud_eras(bdf_path, tmp_path, {'Cenozoic': cenozoic_path}, dummy_logger)

    assert 'Found 1 malformed BDF records during ASUD Era validation.' in dummy_logger.messages


def test_validation_asud_eras_non_base_within_type_skipped(tmp_path, dummy_logger):
    qc_dir = tmp_path / 'qc'
    qc_dir.mkdir()
    bdf_path = qc_dir / 'met2.bdf'
    cenozoic_path = tmp_path / 'cenozoic.csv'

    _write_era_lookup_file(cenozoic_path, [('UnitA', 'N001')])

    # Type that doesn't match BASE_*_TOP_* or WITHIN_* patterns
    bdf_path.write_text(
        _make_bdf_record('UNRECOGNISED_TYPE', over_name='UnitA', over_no='N001') + '\n',
        encoding='utf-8'
    )

    validation.initialise_error_log(qc_dir)
    validation.validation_asud_eras(bdf_path, tmp_path, {'Cenozoic': cenozoic_path}, dummy_logger)

    d = date.today().strftime('%Y%m%d')
    summary = (qc_dir / f'ASUD_age_validation_summary_{d}.txt').read_text(encoding='utf-8')

    assert summary.strip() == 'result,interpretation value,ASUD value,field 1,field 2,strat unit,strat no,count'


def test_validation_asud_eras_multiple_era_files(tmp_path, dummy_logger):
    qc_dir = tmp_path / 'qc'
    qc_dir.mkdir()
    bdf_path = qc_dir / 'met2.bdf'
    cenozoic_path = tmp_path / 'cenozoic.csv'
    paleozoic_path = tmp_path / 'paleozoic.csv'
    mesozoic_path = tmp_path / 'mesozoic.csv'

    _write_era_lookup_file(cenozoic_path, [('UnitA', 'N001')])
    _write_era_lookup_file(paleozoic_path, [('UnitB', 'N002')])
    _write_era_lookup_file(mesozoic_path, [('UnitC', 'N003')])

    bdf_path.write_text(
        _make_bdf_record('BASE_Cenozoic_TOP_Paleozoic', over_name='UnitA', over_no='N001',
                         under_name='UnitB', under_no='N002') + '\n' +
        _make_bdf_record('WITHIN_Mesozoic', within_name='UnitC', within_no='N003') + '\n',
        encoding='utf-8'
    )

    validation.initialise_error_log(qc_dir)
    validation.validation_asud_eras(bdf_path, tmp_path,
                                    {'Cenozoic': cenozoic_path, 'Paleozoic': paleozoic_path,
                                     'Mesozoic': mesozoic_path},
                                    dummy_logger)

    d = date.today().strftime('%Y%m%d')
    summary = (qc_dir / f'ASUD_age_validation_summary_{d}.txt').read_text(encoding='utf-8')

    assert 'matched,Cenozoic,Cenozoic,OvrStrtUnt,OvrStratNo,UnitA,N001,1' in summary
    assert 'matched,Paleozoic,Paleozoic,UndStrtUnt,UndStratNo,UnitB,N002,1' in summary
    assert 'matched,Mesozoic,Mesozoic,WithinStrt,WithinStNo,UnitC,N003,1' in summary
    assert any('Records checked: 2' in msg for msg in dummy_logger.messages)
