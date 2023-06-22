from . import SWD


SCENARIO_SRC = [
        {'dir1' : 
            ['a.txt', 'b.txt', {
            'dir2': [
                'c.csv', 'd.cpp', {
                'venv': [
                    'e.whl', 'f.h']}],
            'dir 4': {'h.html', 'i.ini'},
            'dir5': []
            }, '__k.pdf']
        },
        'g.xml',
        'h.go',
        {'dir3':[]}
    ]
SCENARIO_TGT = [
        {'dir1' : 
            ['a.txt', 'r_ b.txt', {
            'dir2': [
                'c.csv', 'd.cpp', {
                'venv': [
                    'e.whl', 'f.h', 'r_n.exe']}],
            'dir 4': ['h.html', 'r_i.ini'],
            'r_dir5': ['r_j.jpg', 'r_k.rtf']
            }
            ]
        },
        'r_g.xml',
        'g.xml'
    ]


EXP_GEN_RSYNC = [
    '# Sync files',
    'if pgrep some_pid; then',
    '  echo "ERROR some_pid must be closed in order to backup the configuration" >> some/pa\\ th/test.log',
    'else',
    f'  tar -cjf arch.bz2 {SWD}/data/src/dir1',
    'fi',
    f'rsync -truOvn {SWD}/data/src/g.xml . $log ',
    f'rsync -truOvn {SWD}/data/src/'+'{h.go,l.doc} . $log ',
    ''
]

EXP_PREPARE_SCRIPT_ACTIONS = [
'# Apply changes (renamed/deleted/moved)',
'rm -rfv dir1/r_dir5 | tee -a some/pa\\ th/test.log',
'rm -rfv dir1/r_\\ b.txt | tee -a some/pa\\ th/test.log',
'rm -rfv dir1/dir\\ 4/r_i.ini | tee -a some/pa\\ th/test.log',
''
]

EXP_GENERATE_PREPARE_SCRIPT = [
    '#!/usr/bin/env bash',
    '',
    '# Enable Pathname Expansion',
    'shopt -s extglob',
    '',
    '# Setup logging',
    'echo -n > some/pa\\ th/test.log',
    'log="--log-file=some/pa\\ th/test.log --log-file-format=/%f"',
    '',
    '# Create directories',
    'mkdir -p dir1/new_dir',
    '',
    '# Pre Commands',
    "echo 'Goodbye' | tee some/pa\\ th/test.log",
    'man tee',
    '# Apply changes (renamed/deleted/moved)',
    'rm -rfv dir1/dir\\ 4/r_i.ini | tee -a some/pa\\ th/test.log',
    'rm -rfv dir1/r_dir5 | tee -a some/pa\\ th/test.log',
    'rm -rfv dir1/r_\\ b.txt | tee -a some/pa\\ th/test.log',
    '',
    '# Sync files',
    'if pgrep some_pid; then',
    '  echo "ERROR some_pid must be closed in order to backup the configuration" >> some/pa\\ th/test.log',
    'else',
    '  tar -cjf arch.bz2 '
    f'{SWD}/data/src/dir1',
    'fi',
    f'rsync -truOvn {SWD}/data/src/g.xml . $log ',
    'rsync -truOvn '
    f'{SWD}/data/src/' + '{h.go,l.doc} . $log ',
    '',
    '# Post Commands',
    "echo 'Hello, world'"
]
