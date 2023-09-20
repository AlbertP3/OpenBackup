# OpenBackup
A tool for making incremental backups

## Description
This program builds a bash script following settings specified in the configuration file. 'rsync' command is used to track new|modified files and a custom TreeMonitor tracks renames|moves|deletions. Then a generated script is presented to the user for acceptation. It's main purpose is to make incremental backups - all files that are present only on the Destination will be marked for deletion and those created|modified on the Source will overwrite corresponding ones on Destination.

## Usage
<ol>
<li>Go to the backup destination (or set 'defaultdst' parameter instead) and execute make_backup.py
<li>First, the script will load the configuration file. This can be done by:
<ol>
<li>Auto: by matching hostname, looking for 'default.json' or selecting the only available file</li>
<li>Manual: a list of available profiles is presented to be selected by their index</li>
</ol>
<li>Second, a bash script will begin to generate. This can take some time, based on the amount of files to be scanned (~12s/10_000 files)
<li>Then a temporary file with generated instructions is created and presented to the user in a way specified by the 'editor' setting. It can be reviewed and edited at will
<ol>
<li>If 'editor' is specified then it's command is used to present the generated script. If it's saved then the script will be executed (mtime > ctime)
<li>Else generated instructions are printed to stdout and a prompt [Y/n] is displayed. Tempfile can still be modified by hand before accepting
</ol>
<li>Note that no actions took place until this point (i.e delete/copy)
<li>Finally, user can accept or decline execution of the generated script.
</ol>

## Configuration
Configuration is done via json files in the profiles directory. Example profile is included in the repository (test.json). Required parameters are marked with a star. Available parameters are listed below:
```
Parameters in config:
    rsync:
        paths:
           *src             - path to the dir||file on the Source. Supports bracket expansion
            dst             - destination for the backup files. Defaults to defaultdst
            exclude         - rsync glob patterns to ommit matched paths
            isconf          - is configuration, applies rconfmode args
            require_closed  - check if given process is running, using pgrep
            archive         - tar the file/dir and send it to destination
            extract         - untar the file/dir and send it to destination
        settings:
           *rmode           - args for rsync
           *rconfmode       - args for rsync if is_conf
           *rlogfilename    - where to save logs from rsync
           *rlogfileformat  - rsync logs format
            mkdirs          - list of dirs to create before backup begins. Untracked
            defaultdst      - path to recourse to if dst was not provided. Defaults to '.'
            cmd:
                post        - list of commands to run after the backup is done
                pre         - list of commands to run before the backup starts'''
    settings:
        editor:             - command via which the generated script is presented
```
</br>
Contact: psyduckdebugging@gmail.com