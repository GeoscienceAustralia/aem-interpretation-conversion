import csv
import os
from datetime import date
from pathlib import Path

from loguru import logger

BDF_FIELD_NAMES = [
    'FLIGHT_LINE',
    'SHAPEFILE_FID',
    'ARTEFACT',
    'Type',
    'BoundConf',
    'ContactTyp',
    'BasisOfInt',
    'OvrStrtUnt',
    'OvrStratNo',
    'OvrConf',
    'UndStrtUnt',
    'UndStratNo',
    'UndConf',
    'WithinStrt',
    'WithinStNo',
    'WithinConf',
    'HydStrtType',
    'HydStrConf',
    'BOMNAFUnt',
    'BOMNAFNo',
    'InterpRef',
    'Comment',
    'Annotation',
    'NewObs',
    'Operator',
    'Date',
    ]

ERROR_LOG_BDF_FIELD_NAMES = BDF_FIELD_NAMES[:2] + BDF_FIELD_NAMES[3:]

ERROR_LOG_HEADER = [
    'ERROR_GENERAL',
    'ERROR_TYPE',
    'ERROR_FIELD1',
    'ERROR_FIELD1_ENTRY',
    'ERROR_FIELD2',
    'ERROR_FIELD2_ENTRY', 
    'ERROR_COUNT',
    ] + ERROR_LOG_BDF_FIELD_NAMES


def validation_remove_quotes(bdf_file_path, bdf_out_file_path, logger_session=logger):
    logger_session.info("Running remove quotes validation.")
    try:
        with open(bdf_file_path, 'r') as bdf_file, open(bdf_out_file_path, 'w') as bdf_clean_out_file:
            for line in bdf_file:
                bdf_clean_out_file.write(line.replace('"', ''))
        logger_session.info("Completed remove quotes validation.")
    except Exception as e:
        logger_session.error(f"Error during remove quotes validation: {e}")
        raise


def validation_qc_units(erc_file_path, bdf_2_file_path, validation_dir, logger_session=logger):
    logger_session.info("Running qc_units validation.")
    # Initialize dictionaries to store stratigraphic unit information
    stratno = {}
    name = {}
    units = {}
    count = {}
    no_unit = {}

    # Read stratigraphic-unit.csv
    try:
        qc_outputs_path = os.path.join(validation_dir, 'qc') + os.sep
        Path(qc_outputs_path).mkdir(exist_ok=True)

        with open(erc_file_path, "r", encoding='utf-8') as strat_file:
            for line in strat_file:
                fields = line.strip().split("|")
                if len(fields) != 43:
                    with open(fr"{qc_outputs_path}asud_nf.asc", "a") as nf_file:
                        nf_file.write(f"{len(fields)} {line}")
                else:
                    stratno[fields[0]] = fields[1]
                    name[fields[0]] = fields[0]

        # Read AusAEM1_Interp.csv and compare unit name-number
        with open(bdf_2_file_path, "r") as interp_file:
            with open(fr'{qc_outputs_path}error_list.log', "a") as error_list_file:

                for line in interp_file:
                    fields = line.strip().split("|")
                    if len(fields) <= 25:
                        with open(fr"{qc_outputs_path}short_nf.log", "a") as short_nf_file:
                            short_nf_file.write(f"{len(fields)} {fields[0]} {fields[1]}\n")
                        continue

                    if fields[7]:
                        if name.get(fields[7]) == fields[7] and stratno.get(fields[7]) == fields[8]:
                            units[f"{fields[7]} {fields[8]}"] = f"{fields[7]},{fields[8]}"
                            count[f"{fields[7]} {fields[8]}"] = count.get(f"{fields[7]} {fields[8]}", 0) + 1
                        else:
                            no_unit[f"{fields[7]} {fields[8]}"] = f"{fields[7]},{fields[8]}"
                            count[f"{fields[7]} {fields[8]}"] = count.get(f"{fields[7]} {fields[8]}", 0) + 1
                            _write_validation_error(error_list_file, 'over', 'no match', 'OvrStrtUnt', fields[7],
                                                    'OvrStratNo', fields[8], fields)

                    if fields[10]:
                        if name.get(fields[10]) == fields[10] and stratno.get(fields[10]) == fields[11]:
                            units[f"{fields[10]} {fields[11]}"] = f"{fields[10]},{fields[11]}"
                            count[f"{fields[10]} {fields[11]}"] = count.get(f"{fields[10]} {fields[11]}", 0) + 1
                        else:
                            no_unit[f"{fields[10]} {fields[11]}"] = f"{fields[10]},{fields[11]}"
                            count[f"{fields[10]} {fields[11]}"] = count.get(f"{fields[10]} {fields[11]}", 0) + 1
                            _write_validation_error(error_list_file, 'under', 'no match', 'UndStrtUnt', fields[10],
                                                    'UndStratNo', fields[11], fields)

                    if fields[13]:
                        if name.get(fields[13]) == fields[13] and stratno.get(fields[13]) == fields[14]:
                            units[f"{fields[13]} {fields[14]}"] = f"{fields[13]},{fields[14]}"
                            count[f"{fields[13]} {fields[14]}"] = count.get(f"{fields[13]} {fields[14]}", 0) + 1
                        else:
                            no_unit[f"{fields[13]} {fields[14]}"] = f"{fields[13]},{fields[14]}"
                            count[f"{fields[13]} {fields[14]}"] = count.get(f"{fields[13]} {fields[14]}", 0) + 1
                            _write_validation_error(error_list_file, 'within', 'no match', 'WithinStrt', fields[13],
                                                    'WithinStNo', fields[14], fields)

        d = date.today().strftime("%Y%m%d")
        summary_file = fr'{qc_outputs_path}ASUD_validation_summary_{d}.txt'

        with open(summary_file, "w") as summary_file:
            logger_session.info("result,name,number,count")
            summary_file.write('result,name,number,count\n')
            for var in units:
                logger_session.info(f"matched,{units[var]},{count[var]}")
                summary_file.write(f'matched,{units[var]},{count[var]}\n')

            for var in no_unit:
                logger_session.info(f"no match,{no_unit[var]},{count[var]}")
                summary_file.write(f'no match,{no_unit[var]},{count[var]}\n')

        logger_session.info("completed qc_units validation.")
    except Exception as e:
        logger_session.error(f"Error during qc_units validation: {e}")


def validation_mandatory_fields(confidence_lookup_path, contact_type_lookup_path, interpretation_basis_lookup_path,
                                bdf_2_file_path, validation_dir, logger_session=logger):
    logger_session.info("Running mandatory field validation.")

    try:
        confidence_values = _load_lookup_values(confidence_lookup_path)
        contact_type_values = _load_lookup_values(contact_type_lookup_path)
        interp_basis_values = _load_lookup_values(interpretation_basis_lookup_path)

        qc_outputs_path = os.path.join(validation_dir, 'qc') + os.sep
        Path(qc_outputs_path).mkdir(parents=True, exist_ok=True)

        d = date.today().strftime("%Y%m%d")
        confidence_summary_file = fr'{qc_outputs_path}Confidence_validation_summary_{d}.txt'
        contact_summary_file = fr'{qc_outputs_path}Contact_type_validation_summary_{d}.txt'
        interpretation_basis_summary_file = fr'{qc_outputs_path}Interpretation_basis_validation_summary_{d}.txt'
        comma_summary_file = fr'{qc_outputs_path}Comma_validation_summary_{d}.txt'
        error_list_path = fr'{qc_outputs_path}error_list.log'

        confidence_summary = {}
        contact_summary = {}
        interp_basis_summary = {}
        comma_summary = {}

        confidence_rules = {
            'BoundConf': {'field_index': 4, 'related_unit_index': None},
            'OvrConf': {'field_index': 9, 'related_unit_index': 7},
            'UndConf': {'field_index': 12, 'related_unit_index': 10},
            'WithinConf': {'field_index': 15, 'related_unit_index': 13},
        }

        record_count = 0
        confidence_error_count = 0
        contact_error_count = 0
        interp_basis_error_count = 0
        comma_error_count = 0
        malformed_record_count = 0

        with (open(bdf_2_file_path, 'r', encoding='utf-8', errors='replace') as bdf_file,
              open(error_list_path, 'a', encoding='utf-8') as error_list_file):
            for line in bdf_file:
                record_count += 1
                record_line = line.rstrip('\r\n')
                fields = record_line.split('|')

                if len(fields) != 26:
                    malformed_record_count += 1
                    _write_validation_error(error_list_file, 'bdf', 'incorrect field count', 'BDFFieldCount',
                                            str(len(fields)), 'N/A', 'N/A', fields)
                    continue

                for field_index, field_value in enumerate(fields):
                    if ',' not in field_value:
                        continue

                    comma_error_count += 1
                    comma_field_name = BDF_FIELD_NAMES[field_index]
                    comma_key = (comma_field_name, 'comma found', field_value)
                    comma_summary[comma_key] = comma_summary.get(comma_key, 0) + 1
                    _write_validation_error(error_list_file, 'comma', 'comma found', comma_field_name, field_value,
                                            'N/A', 'N/A', fields)

                for field_name, validation_rule in confidence_rules.items():
                    field_index = validation_rule['field_index']
                    related_unit_index = validation_rule['related_unit_index']
                    value = fields[field_index].strip()
                    field_is_required = related_unit_index is None or bool(fields[related_unit_index].strip())

                    if not value:
                        result = 'missing' if field_is_required else 'blank allowed'
                    elif value in confidence_values:
                        result = 'matched'
                    else:
                        result = 'no match'

                    confidence_key = (field_name, result, value)
                    confidence_summary[confidence_key] = confidence_summary.get(confidence_key, 0) + 1

                    if result in {'missing', 'no match'}:
                        confidence_error_count += 1
                        _write_validation_error(error_list_file, 'confidence', result, field_name,
                                                value or '<blank>', 'N/A', 'N/A', fields)

                contact_type = fields[5].strip()

                if not contact_type:
                    contact_result = 'missing'
                elif contact_type in contact_type_values:
                    contact_result = 'matched'
                else:
                    contact_result = 'no match'

                contact_key = ('ContactTyp', contact_result, contact_type)
                contact_summary[contact_key] = contact_summary.get(contact_key, 0) + 1

                if contact_result in {'missing', 'no match'}:
                    contact_error_count += 1
                    _write_validation_error(error_list_file, 'contact type', contact_result, 'ContactTyp',
                                            contact_type or '<blank>', 'N/A', 'N/A', fields)

                interp_basis = fields[6].strip()

                if not interp_basis:
                    interp_basis_error_count += 1
                    interp_basis_key = ('BasisOfInt', 'missing', '')
                    interp_basis_summary[interp_basis_key] = interp_basis_summary.get(interp_basis_key, 0) + 1
                    _write_validation_error(error_list_file, 'interpretation basis', 'missing', 'BasisOfInt', '<blank>',
                                            'N/A', 'N/A', fields)
                else:
                    basis_values = interp_basis.split(';')

                    for basis_value in basis_values:
                        basis_value = basis_value.strip()
                        basis_result = 'matched' if basis_value and basis_value in interp_basis_values else 'no match'
                        interp_basis_key = ('BasisOfInt', basis_result, basis_value)
                        interp_basis_summary[interp_basis_key] = interp_basis_summary.get(interp_basis_key, 0) + 1

                        if basis_result == 'no match':
                            interp_basis_error_count += 1
                            _write_validation_error(error_list_file, 'interpretation basis', 'no match', 'BasisOfInt',
                                                    basis_value or '<blank>', 'N/A', 'N/A', fields)

        if malformed_record_count:
            logger_session.warning(f'Found {malformed_record_count} malformed BDF records.')

        _write_validation_summary(confidence_summary_file, confidence_summary, logger_session)
        _write_validation_summary(contact_summary_file, contact_summary, logger_session)
        _write_validation_summary(interpretation_basis_summary_file, interp_basis_summary, logger_session)
        _write_validation_summary(comma_summary_file, comma_summary, logger_session)

        logger_session.info(f'Completed mandatory field validation. Records checked: {record_count}. '
                            f'Confidence errors:{confidence_error_count}. '
                            f'Contact type errors: {contact_error_count}. '
                            f'Interpretation basis errors: {interp_basis_error_count}. '
                            f'Comma errors: {comma_error_count}. '
                            f'Malformed records: {malformed_record_count}. ')

    except Exception as e:
        logger_session.error(f'Error during mandatory field validation: {e}')
        raise


def _write_validation_summary(summary_file_path, validation_summary, logger_session=logger):
    with open(summary_file_path, 'w', encoding='utf-8', newline='') as summary_file:
        writer = csv.writer(summary_file)
        writer.writerow(['result', 'field', 'value', 'count'])

        for summary_key, count in validation_summary.items():
            field, result, value = summary_key
            logger_session.info(f'{result},{field},{value},{count}')
            writer.writerow([result, field, value, count])


def initialise_error_log(qc_dir):
    error_list_path = Path(qc_dir) / 'error_list.log'
    error_list_path.write_text('|'.join(ERROR_LOG_HEADER) + '\n', encoding='utf-8')


def _write_validation_error(error_list_file, error_general, error_type, error_field1, error_field1_entry, error_field2,
                            error_field2_entry, fields):
    bdf_fields = fields[:26] + [''] * max(0, 26 - len(fields))
    error_bdf_fields = bdf_fields[:2] + bdf_fields[3:]
    error_list_file.write('|'.join([error_general, error_type, error_field1, error_field1_entry,
                                    error_field2, error_field2_entry, ''] + error_bdf_fields) + '\n')


def finalise_error_log(qc_dir):
    error_list_path = Path(qc_dir) / 'error_list.log'

    with open(error_list_path, 'r', encoding='utf-8') as error_list_file:
        lines = error_list_file.readlines()

    header = lines[0]
    rows = [line.rstrip('\n').split('|') for line in lines[1:]]

    error_counts = {}

    for row in rows:
        point_key = (row[7], row[8])
        error_counts[point_key] = error_counts.get(point_key, 0) + 1

    with open(error_list_path, 'w', encoding='utf-8') as error_list_file:
        error_list_file.write(header)

        for row in rows:
            point_key = (row[7], row[8])
            row[6] = str(error_counts[point_key])
            error_list_file.write('|'.join(row) + '\n')


def _load_lookup_values(lookup_file_path):
    lookup_values = set()

    with open(lookup_file_path, "r", encoding="utf-8") as lookup_file:
        next(lookup_file, None)

        for line in lookup_file:
            line = line.strip()

            if line:
                lookup_values.add(line.split(maxsplit=1)[0])

    if not lookup_values:
        raise ValueError(f"No values found in lookup file: {lookup_file_path}")

    return lookup_values


def main(input_directory, output_directory, asud, confidence_lookup, contact_type_lookup, interpretation_basis_lookup):
    bdf_file_path = fr'{output_directory}{os.sep}interp{os.sep}met.bdf'
    qc_output_dir = fr'{output_directory}{os.sep}qc'

    Path(fr'{output_directory}{os.sep}qc').mkdir(exist_ok=True)
    bdf_out_file_path = fr'{qc_output_dir}{os.sep}met2.bdf'

    validation_remove_quotes(bdf_file_path, bdf_out_file_path)
    initialise_error_log(qc_output_dir)

    erc_file_path = os.path.join(input_directory, asud)
    confidence_lookup_path = os.path.join(input_directory, confidence_lookup)
    contact_type_lookup_path = os.path.join(input_directory, contact_type_lookup)
    interpretation_basis_lookup_path = os.path.join(input_directory, interpretation_basis_lookup)

    validation_qc_units(erc_file_path, bdf_out_file_path, output_directory)
    validation_mandatory_fields(confidence_lookup_path, contact_type_lookup_path, interpretation_basis_lookup_path,
                                bdf_out_file_path, output_directory)
    finalise_error_log(qc_output_dir)


if __name__ == "__main__":
    main()
