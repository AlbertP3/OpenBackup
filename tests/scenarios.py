from . import SWD, DDP


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
        {'dir3':[]},
        {'dir6': ['z.zip', 'b.bz2', {'dir7': ['t.tar']}]}
    ]
SCENARIO_TGT = [
        {'dir1' : 
            ['a.txt', 'r_ b.txt', {
            'dir2': [
                'c.csv', 'd.cpp', {
                'venv': [
                    'e.whl', 'f.h', 'r_n.exe']}],
            'dir 4': ['h.html', 'r_i.ini'],
            'r_dir5': ['r_j.jpg', 'r_k.rtf'],
            'conf': ['r_e.avi', 'h.go', {
                'r_dig': [
                    'r_z.zip'
                ]
            }
            ]
            }
            ]
        },
        'r_g.xml',
        'g.xml'
    ]


EXP_GEN_RSYNC = [
    '# Sync files',
    f'rsync -truOvn {SWD}/data/src/dir1 {DDP} $log ' + '--exclude={*/venv*,*/__.*}',
    'if pgrep some_pid; then',
    '  echo "ERROR some_pid must be closed in order to backup the configuration" >> some/pa\\ th/test.log',
    'else',
    f'  tar -cf dir1/arch.tar {SWD}/data/src/dir6 | tee -a some/pa\\ th/test.log',
    'fi',
    f'rsync -truOvn {SWD}/data/src/g.xml {DDP} $log ',
    f'rsync -truOvn {SWD}/data/src/'+'{h.go,l.doc} tests/data/tgt/dir1/conf $log ',
    ''
]

EXP_PREPARE_SCRIPT_ACTIONS = [
'# Apply changes (renamed/deleted/moved)',
f'rm -rfv {DDP}/dir1/dir\\ 4/r_i.ini | tee -a some/pa\\ th/test.log',
f'rm -rfv {DDP}/dir1/r_\\ b.txt | tee -a some/pa\\ th/test.log',
f'rm -rfv {DDP}/dir1/r_dir5 | tee -a some/pa\\ th/test.log',
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
    'mkdir -p tests/data/tgt/adj',
    '',
    '# Pre Commands',
    "echo 'Goodbye' | tee some/pa\\ th/test.log",
    'man tee',
    '',
    '# Apply changes (renamed/deleted/moved)',
    f'rm -rfv {DDP}/dir1/dir\\ 4/r_i.ini | tee -a some/pa\\ th/test.log',
    f'rm -rfv {DDP}/dir1/r_\\ b.txt | tee -a some/pa\\ th/test.log',
    f'rm -rfv {DDP}/dir1/r_dir5 | tee -a some/pa\\ th/test.log',
    '',
    '# Sync files',
    f'rsync -truOvn {SWD}/data/src/dir1 {DDP} $log ' + '--exclude={*/venv*,*/__.*}',
    'if pgrep some_pid; then',
    '  echo "ERROR some_pid must be closed in order to backup the configuration" >> some/pa\\ th/test.log',
    'else',
    f'  tar -cf dir1/arch.tar {SWD}/data/src/dir6 | tee -a some/pa\\ th/test.log',
    'fi',
    f'rsync -truOvn {SWD}/data/src/g.xml {DDP} $log ',
    f'rsync -truOvn {SWD}/data/src/' + '{h.go,l.doc} tests/data/tgt/dir1/conf $log ',
    '',
    '# Post Commands',
    "echo 'Hello, world'",
    ''
]
