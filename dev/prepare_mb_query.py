#!/usr/bin/env python3

""" Mirrorbrain configuration update SQL query prep script

This script is meant to be used to prepare an SQL command to update mirrorbrain'
servers configuration (in its postgres DB)

User must first retrieve and download in JSON format the table from mirrors-qa at
https://mirrors-qa.kiwix.org/question/38-mirrorbrain-configuration-table
"""


import sys
import json
import pathlib
import re

def main(json_path: pathlib.Path) -> int:
    mqa_config = json.loads(json_path.read_bytes())
    for mdata in mqa_config:
        identifier = mdata["mirror_id"]
        region = mdata["region"]
        country = mdata["country"]
        score = int(float(mdata["score"].replace(",", "")))
        region_only = mdata["region_only"] == "true"
        other_countries = re.sub(r"}$", "", re.sub(r"^{", "", mdata["other_countries"]))

        query = f"""UPDATE public.server
        SET
            region='{region}',
            country='{country}',
            score={score},
            region_only={region_only!s},
            other_countries='{other_countries}'
        WHERE server.identifier='{identifier}';
        """

        print(query)


    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} metabase-export.json")
        sys.exit(1)
    sys.exit(main(pathlib.Path(sys.argv[1]).expanduser().resolve()))
