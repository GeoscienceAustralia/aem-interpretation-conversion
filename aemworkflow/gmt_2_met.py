
import argparse
import re
from pathlib import Path


def main(directory: str, suffix: str) -> None:
    """
    """
    pdir = Path(directory)
    files = sorted(pdir.glob(".".join(["*", suffix])))
    # print(*files)
    fid = 0
    ai = 1
    for _i, _f in enumerate(files, 1):
        with open(_f, "r") as fin:
            # print(_f)
            for line in fin:
                part = line.split("|")
                # strip the double quotes where present
                part = [_s.strip('\"') if '\"' in _s else _s for _s in part]
                # print(part[0])
                if re.search("@D", part[0]):
                    if (_i == ai):
                        print(f"{_f}|{fid}|{'|'.join(part[0:24])}", end="")
                        fid += 1
                    else:
                        ai = _i
                        fid = 0
                        print(f"{_f}|{fid}|{'|'.join(part[0:24])}", end="")
                        fid += 1


"""
{
  if ($1 ~ /@D/){
   if(ARGIND==ai){
   print FILENAME"|"fid"|"$1"|"$2"|"$3"|"$4"|"$5"|"$6"|"$7"|"$8"|"$9"|"$10"|
   "$11"|"$12"|"$13"|"$14"|"$15"|"$16"|"$17"|"$18"|"$19"|"$20"|"$21"|"$22"|"$23"|"$24
   fid++
   }
  else{
  ai=ARGIND
   fid=0
   print FILENAME"|"fid"|"$1"|"$2"|"$3"|"$4"|"$5"|"$6"|"$7"|"$8"|"$9"|"$10"|
   "$11"|"$12"|"$13"|"$14"|"$15"|"$16"|"$17"|"$18"|"$19"|"$20"|"$21"|"$22"|"$23"|"$24
   fid++
   }
  }
}
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", "-s", required=True, help="The common suffix of the file group to process")
    ap.add_argument("--directory", "-d", required=True, help="The directory with the group of files to process")
    ARG = vars(ap.parse_args())
    main(ARG["directory"], ARG["suffix"])
