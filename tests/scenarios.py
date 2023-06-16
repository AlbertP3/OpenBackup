
SCENARIO_SRC = [
        {'dir1' : 
            ['a.txt', 'b.txt', {
            'dir2': [
                'c.csv', 'd.cpp', {
                'venv': [
                    'e.whl', 'f.h']}],
            'dir4': {'h.html', 'i.ini'},
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
            'dir4': ['h.html', 'r_i.ini'],
            'r_dir5': ['r_j.jpg', 'r_k.rtf']
            }
            ]
        },
        'r_g.xml',
        'g.xml'
    ]
