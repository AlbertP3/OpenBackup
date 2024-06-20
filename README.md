# OpenBackup

## Description
Main purpose of this application is to make incremental backups. In order to achieve it, the program builds an executable script by following settings specified in the selected config file and unless reviewed and accepted by the user, this script will not be executed. The Tool (rsync|python) is used to track (new|modified) files and a custom Monitor tracks (renames|moves|deletions)

## Usage
1. Go to the backup destination (or set 'defaultdst' parameter instead) and execute make_backup.py
2. First, the script will load the configuration file. This can be done by:
   1. Auto: by matching hostname, looking for 'default.json' or selecting the only available file
   2. Manual: a list of available profiles is presented to be selected by their index
3. Second, a script will begin to generate. This can take some time, based on the amount of files to be scanned
4. Then a temporary file with generated instructions is created and presented to the user in a way specified by the 'editor' setting. It can be reviewed and edited at will
   1. If 'editor' is specified then it's command is used to present the generated script. If it's saved then the script will be executed (mtime > ctime)
   2. Else a prompt is displayed and the tmpfile can still be modified in an external editor before accepting
5. Note that no operations took place until this point (i.e delete/copy/...)
6. Finally, user can accept or decline execution of the generated script

## Available OS
| OS      | Script  | Tool   | Status |
|---      |---      |---     |---     |
| Python  | .py     | -      | WIP    |
| Linux   | .sh     | rsync  | ✅     |
| Windows | -       | -      | N/A    |
| Darwin  | -       | -      | N/A    |

## Configuration
Configuration is done via json files in the profiles directory. Example profile is included in the repository (test.json). Required parameters are marked with a star
```
paths:
    [
        {
            *src                - path to the dir or file on the Source. Supports bracket expansion
            dst                 - destination for the backup files. Defaults to 'defaultdst'
            exclude             - glob patterns to ommit matched paths
            isconf              - is configuration, applies rconfmode args
            require_closed      - check if a given process is running
            archive             - boolean, create an archive. Determines compression based on filename
            extract             - boolean, extract from archive. Determines compression based on filename
        },
        {...}
    ]
settings:
    {
        *rmode                  - args for the Tool
        *rconfmode              - args for the Tool if 'is_conf'
        *logfile                - location to save logs
        *logfmt                 - the Tool logs format
        *cmd:
            *post               - list of commands to run after the backup is done
            *pre                - list of commands to run before the backup starts
        os                      - which OS-specific Tool to use. Defaults to 'python'            
        name                    - prefix for tmp script file. Defaults to 'job'
        editor                  - command via which the script is presented. Defaults to y/n prompt
        mkdirs                  - list of dirs to create before backup begins. Untracked
        defaultdst              - path to recourse to if 'dst' was not provided. Defaults to '.'
        sync_precision          - tolerance in seconds for mtime differences. Defaults to 1
        shebang                 - allows to customize the script's shebang
        validate                - verify generated script has correct synthax. Defaults to True
    }
```

## Contact
psyduckdebugging@gmail.com