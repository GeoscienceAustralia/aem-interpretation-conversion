# import sys
import os
# from pathlib import Path
# import glob
# import pandas as pd
# import re

# from loguru import logger
from datetime import date
# from typing import List, Tuple
# from aemworkflow.webapp.config import get_ogr_path


def validation_remove_quotes(bdf_file_path, bdf_out_file_path, logger_session):
    logger_session.info("Running remove quotes validation.")
    with open(bdf_file_path, 'r') as bdf_file, open(bdf_out_file_path, 'w') as bdf_clean_out_file:
        for line in bdf_file:
            bdf_clean_out_file.write(line.replace('"', ''))
    logger_session.info("Completed remove quotes validation.")


def validation_qc_units(erc_file_path, bdf_2_file_path, validation_dir, logger_session):
    logger_session.info("Running qc_units validation.")
    # Initialize dictionaries to store stratigraphic unit information
    stratno = {}
    name = {}
    units = {}
    count = {}
    no_unit = {}

    # Read stratigraphic-unit.csv
    with open(erc_file_path, "r", encoding='utf-8') as strat_file:
        for line in strat_file:
            fields = line.strip().split("|")
            if len(fields) != 43:
                with open("asud_nf.asc", "a") as nf_file:
                    nf_file.write(f"{len(fields)} {line}")
                    # nf_file.write(f"{len(fields)} {NR} {line}")
            else:
                stratno[fields[0]] = fields[1]
                name[fields[0]] = fields[0]

    # Read AusAEM1_Interp.csv and compare unit name-number
    with open(bdf_2_file_path, "r") as interp_file:
        with open(fr'{validation_dir}{os.sep}qc{os.sep}error_list.log', "a") as error_list_file:

            for line in interp_file:
                fields = line.strip().split("|")
                if len(fields) <= 25:
                    with open(fr"{validation_dir}{os.sep}qc{os.sep}short_nf.log", "a") as short_nf_file:
                        short_nf_file.write(f"{len(fields)} {fields[0]} {fields[1]}\n")

                if fields[7] == '' and fields[8] == '':
                    if fields[10] == '' and fields[11] == '':
                        if fields[13] == '' and fields[14] == '':
                            units[f"{fields[7]} {fields[8]}"] = f"{fields[7]},{fields[8]}"
                            count[f"{fields[7]} {fields[8]}"] = count.get(f"{fields[7]} {fields[8]}", 0) + 1
                            error_list_file.write(f"nulls|{fields[7]}|{fields[8]}|{line}")
                            continue

                if (name.get(fields[7]) == fields[7] and stratno.get(fields[7]) == fields[8]) or \
                    (name.get(fields[10]) == fields[10] and stratno.get(fields[10]) == fields[11]) or \
                        (name.get(fields[13]) == fields[13] and stratno.get(fields[13]) == fields[14]):

                    if name.get(fields[7]) == fields[7] and stratno.get(fields[7]) == fields[8]:
                        units[f"{fields[7]} {fields[8]}"] = f"{fields[7]},{fields[8]}"
                        count[f"{fields[7]} {fields[8]}"] = count.get(f"{fields[7]} {fields[8]}", 0) + 1
                    else:
                        no_unit[f"{fields[7]} {fields[8]}"] = f"{fields[7]},{fields[8]}"
                        count[f"{fields[7]} {fields[8]}"] = count.get(f"{fields[7]} {fields[8]}", 0) + 1
                        error_list_file.write(f"over|{fields[7]}|{fields[8]}|{line}")

                    if name.get(fields[10]) == fields[10] and stratno.get(fields[10]) == fields[11]:
                        units[f"{fields[10]} {fields[11]}"] = f"{fields[10]},{fields[11]}"
                        count[f"{fields[10]} {fields[11]}"] = count.get(f"{fields[10]} {fields[11]}", 0) + 1
                    else:
                        no_unit[f"{fields[10]} {fields[11]}"] = f"{fields[10]},{fields[11]}"
                        count[f"{fields[10]} {fields[11]}"] = count.get(f"{fields[10]} {fields[11]}", 0) + 1
                        error_list_file.write(f"under|{fields[10]}|{fields[11]}|{line}")

                    if name.get(fields[13]) == fields[13] and stratno.get(fields[13]) == fields[14]:
                        units[f"{fields[13]} {fields[14]}"] = f"{fields[13]},{fields[14]}"
                        count[f"{fields[13]} {fields[14]}"] = count.get(f"{fields[13]} {fields[14]}", 0) + 1
                    else:
                        no_unit[f"{fields[13]} {fields[14]}"] = f"{fields[13]},{fields[14]}"
                        count[f"{fields[13]} {fields[14]}"] = count.get(f"{fields[13]} {fields[14]}", 0) + 1
                        error_list_file.write(f"within|{fields[13]}|{fields[14]}|{line}")

                else:
                    # No match at all
                    no_unit[f'{fields[7]} {fields[8]}'] = f'{fields[7]},{fields[8]}'
                    no_unit[f'{fields[10]} {fields[11]}'] = f'{fields[10]},{fields[11]}'
                    no_unit[f'{fields[13]} {fields[14]}'] = f'{fields[13]},{fields[14]}'

                    count[f'{fields[7]} {fields[8]}'] = count.get(f'{fields[7]} {fields[8]}', 0) + 1
                    count[f'{fields[10]} {fields[11]}'] = count.get(f'{fields[10]} {fields[11]}', 0) + 1
                    count[f'{fields[13]} {fields[14]}'] = count.get(f'{fields[13]} {fields[14]}', 0) + 1

                    error_list_file.write(f'over|{fields[7]}|{fields[8]}|{line}')
                    error_list_file.write(f'under|{fields[10]}|{fields[11]}|{line}')
                    error_list_file.write(f'within|{fields[13]}|{fields[14]}|{line}')

    d = date.today().strftime("%Y%m%d")
    summary_file = fr'{validation_dir}{os.sep}qc{os.sep}AEM_validation_summary_{d}.txt'

    with open(summary_file, "a") as summary_file:
        logger_session.info("result,name,number,count")
        summary_file.write('result,name,number,count\n')
        for var in units:
            logger_session.info(f"matched,{units[var]},{count[var]}")
            summary_file.write(f'matched,{units[var]},{count[var]}\n')

        for var in no_unit:
            logger_session.info(f"no match,{no_unit[var]},{count[var]}")
            summary_file.write(f'no match,{no_unit[var]},{count[var]}\n')

    logger_session.info("completed qc_units validation.")


# def main():
#     # quotes and qc_units function calls
#     validation_dir = r'C:\Temp\jira-pv-1863\input\validation'
#     bdf_file_path = fr'{validation_dir}\met.bdf'
#     erc_file_path = fr'{validation_dir}\ERC_Stratigraphic_names_Current.txt'
#     bdf_2_file_path = fr'{validation_dir}\qc\met2.bdf'
#     validation_remove_quotes(bdf_file_path)
#     validation_qc_units(erc_file_path, bdf_2_file_path, validation_dir)

#     # zedfix function call
#     # work_dir = r'C:\Temp\jira-pv-1863\input\validation\zedfix\python_in_progress_sample_mundi'
#     # path_dir = work_dir
#     # combined_ext_file_path = r'C:\Temp\jira-pv-1863\input\validation\zedfix\
# python_in_progress_sample_mundi\active_extent.txt'
#     # return_list = validation_zedfix_gmt_to_srt(work_dir, path_dir, combined_ext_file_path)
#     # logger.info(f'return list: {return_list}')

#     # sort functoin call
#     # work_dir = r'C:\Temp\jira-pv-1863\input\validation\sort_gmtp\python_in_progress_sample_mundi'
#     # nm_list = [10300]
#     # validation_sort_gmtp(work_dir, nm_list)

#     logger.info('Completed!!!')


# if __name__ == "__main__":
#     main()
