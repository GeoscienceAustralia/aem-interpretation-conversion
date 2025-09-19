import os
import sys
import shutil
import subprocess  # nosec B404: subprocess usage is controlled and arguments are not user-supplied

from loguru import logger
from typing import List
from pathlib import Path


def get_ogr_path():
    return "ogr2ogr.exe" if os.name == 'nt' else "ogr2ogr"


def validate_file(filepath: str, logger_session=logger) -> bool:
    """
    Validates that the provided shapefile path is a valid file and not user-supplied arbitrary input
    """
    if not Path(filepath).is_file():
        logger_session.error(f"Invalid file path: {filepath}")
        return False
    return True


def run_command(cmd: List[str], logger_session=logger) -> None:
    """
    A helper function to run subprocess commands with error handling.
    WARNING: Ensure that 'cmd' is constructed only from trusted sources to avoid security risks.
    This implementation validates the executable, resolves it via PATH if necessary,
    ensures all args are strings, performs basic sanitisation and then runs without a shell.
    """
    if not cmd or not isinstance(cmd, list) or not all(isinstance(c, str) for c in cmd):
        logger.error("Command must be a non-empty list of strings.")
        sys.exit(1)

    exe = cmd[0]
    exe_path = Path(exe)
    if not exe_path.is_file():
        resolved = shutil.which(exe)
        if resolved:
            cmd[0] = resolved
            exe_path = Path(resolved)
        else:
            logger_session.error(f"Executable not found or not a file: {exe}")
            sys.exit(1)

    if not os.access(str(exe_path), os.X_OK):
        logger_session.error(f"Executable is not executable: {exe_path}")
        sys.exit(1)

    forbidden_chars = set(';|&$`<>')
    for arg in cmd[1:]:
        if any(ch in arg for ch in forbidden_chars):
            logger_session.error(f"Suspicious character found in argument: {arg}")
            sys.exit(1)

    try:
        subprocess.run(cmd, check=True, shell=False)  # nosec B603: subprocess security managed above
    except subprocess.CalledProcessError as e:
        logger_session.error(f"Command '{' '.join(cmd)}' failed with error: {e}")
        sys.exit(1)


def get_make_srt_dir(wrk_dir: str, logger_session=logger) -> None:
    '''
    '''
    try:
        if not (wrk_dir).exists():
            logger_session.info('Making SORT directory...')
            wrk_dir.mkdir()
    except OSError as osx:
        logger_session.error(osx.args)
        sys.exit()
