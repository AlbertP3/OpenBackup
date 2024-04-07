from . import SWD, DDP


SCENARIO_SRC = [
    {
        "dir1": [
            "a.txt",
            "b.txt",
            {
                "dir2": ["c.csv", "d.cpp", {"venv": ["e.whl", "f.h"]}],
                "dir 4": {"h.html", "i.ini"},
                "dir5": [],
            },
            "__k.pdf",
        ]
    },
    "g.xml",
    "h.go",
    {"dir3": []},
    {"dir6": ["z.zip", "b.bz2", {"dir7": ["t.tar", "__r.rar"]}]},
]
SCENARIO_TGT = [
    {
        "dir1": [
            "a.txt",
            "r_ b.txt",
            {
                "dir2": ["c.csv", "d.cpp", {"venv": ["e.whl", "f.h", "r_n.exe"]}],
                "dir 4": ["h.html", "r_i.ini"],
                "r_dir5": ["r_j.jpg", "r_k.rtf"],
                "conf": ["r_e.avi", "h.go", {"r_dig": ["r_z.zip"]}],
            },
        ]
    },
    "r_g.xml",
    "g.xml",
]
EXPECTED_TGT_TREE = {
    f"{DDP}/adj",
    f"{DDP}/r_g.xml",
    f"{DDP}/g.xml",
    f"{DDP}/r_g.xml",
    f"{DDP}/dir1",
    f"{DDP}/dir1/a.txt",
    f"{DDP}/dir1/b.txt",
    f"{DDP}/dir1/arch.tar",
    f"{DDP}/dir1/__k.pdf",
    f"{DDP}/dir1/dir2",
    f"{DDP}/dir1/dir2/d.cpp",
    f"{DDP}/dir1/dir2/venv",
    f"{DDP}/dir1/dir2/venv/e.whl",
    f"{DDP}/dir1/dir2/venv/f.h",
    f"{DDP}/dir1/dir2/venv/r_n.exe",
    f"{DDP}/dir1/dir2/c.csv",
    f"{DDP}/dir1/dir 4",
    f"{DDP}/dir1/dir 4/h.html",
    f"{DDP}/dir1/dir 4/i.ini",
    f"{DDP}/dir1/dir5",
    f"{DDP}/dir1/conf",
    f"{DDP}/dir1/conf/r_dig",
    f"{DDP}/dir1/conf/r_dig/r_z.zip",
    f"{DDP}/dir1/conf/h.go",
    f"{DDP}/dir1/conf/r_e.avi",
}

_log_ref = r'"${log[@]}"'

EXP_GEN_RSYNC = [
    "# Sync files",
    f"rsync -truOv '{SWD}/data/src/dir1' '{DDP}' {_log_ref}"
    + " --exclude='{*/venv*,*/__.*}'",
    "if pgrep 'some_pid'; then",
    "\techo 'ERROR some_pid must be closed in order to backup the configuration' >> 'some/pa th/test.log'",
    "else",
    f"\ttar --exclude='*/__.*' -cvf 'tests/data/tgt/dir1/arch.tar' -C '{SWD}/data/src/dir6' . &>> 'some/pa th/test.log'",
    "fi",
    f"rsync -truOv '{SWD}/data/src/g.xml' '{DDP}' {_log_ref}",
    f"rsync -truOv '{SWD}/data/src/"
    + "{h.go,l.doc}' 'tests/data/tgt/dir1/conf' "
    + _log_ref,
    "",
]

EXP_PREPARE_SCRIPT_ACTIONS = [
    "# Apply changes (renamed/deleted/moved)",
    f"rm -rfv '{DDP}/dir1/dir 4/r_i.ini' | tee -a 'some/pa th/test.log'",
    f"rm -rfv '{DDP}/dir1/r_ b.txt' | tee -a 'some/pa th/test.log'",
    f"rm -rfv '{DDP}/dir1/r_dir5' | tee -a 'some/pa th/test.log'",
    "",
]

EXP_GENERATE_PREPARE_SCRIPT = [
    "#!/bin/bash",
    "",
    "# Enable Pathname Expansion",
    "shopt -s extglob",
    "",
    "# Setup logging",
    "echo -n > 'some/pa th/test.log'",
    """log=(--log-file='some/pa th/test.log' --log-file-format='%f -> %n')""",
    "",
    "# Create directories",
    "mkdir -p 'tests/data/tgt/adj'",
    "",
    "# Pre Commands",
    "echo 'Goodbye' | tee -a 'some/pa th/test.log'",
    "",
    "# Apply changes (renamed/deleted/moved)",
    f"rm -rfv '{DDP}/dir1/dir 4/r_i.ini' | tee -a 'some/pa th/test.log'",
    f"rm -rfv '{DDP}/dir1/r_ b.txt' | tee -a 'some/pa th/test.log'",
    f"rm -rfv '{DDP}/dir1/r_dir5' | tee -a 'some/pa th/test.log'",
    "",
    "# Sync files",
    f"rsync -truOv '{SWD}/data/src/dir1' '{DDP}' {_log_ref}"
    + " --exclude='{*/venv*,*/__.*}'",
    "if pgrep 'some_pid'; then",
    "\techo 'ERROR some_pid must be closed in order to backup the configuration' >> 'some/pa th/test.log'",
    "else",
    f"\ttar --exclude='*/__.*' -cvf 'tests/data/tgt/dir1/arch.tar' -C '{SWD}/data/src/dir6' . &>> 'some/pa th/test.log'",
    "fi",
    f"rsync -truOv '{SWD}/data/src/g.xml' '{DDP}' {_log_ref}",
    f"rsync -truOv '{SWD}/data/src/"
    + "{h.go,l.doc}' 'tests/data/tgt/dir1/conf' "
    + _log_ref,
    "",
    "# Post Commands",
    "sed -i '/ building\\| sent\\|total size/d' 'some/pa th/test.log'",
    "",
]
