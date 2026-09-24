EASYLEARN BACKUP TOOLS
======================

Purpose
-------
This tool creates a dated backup containing:

- the EasyLearn source code and local data files;
- the complete mathsy_db MySQL database;
- a manifest containing the installed software versions.

It does not change or delete the working EasyLearn project.

Installation
------------
Copy these files into:

C:\Users\User\Documents\EasyLearn_Combined

- Backup-EasyLearn.cmd
- Backup-EasyLearn.ps1
- BACKUP-README.txt
- PROJECT-STATUS.md

How to run it
-------------
1. Install and test the newest EasyLearn fixes first.
2. Confirm MySQL80 is Running.
3. Close the EasyLearn service windows so files are not changing.
4. Double-click Backup-EasyLearn.cmd.
5. Press Enter to use the default MySQL username "root", or enter another
   MySQL username.
6. Enter the MySQL password when requested. The password is not displayed and
   is not stored by the script.
7. Wait for BACKUP COMPLETED AND VERIFIED.

The backup is created beside the EasyLearn_Combined folder:

C:\Users\User\Documents\EasyLearn_Backups\EasyLearn_Backup_YYYYMMDD_HHMMSS

Why some folders are excluded
-----------------------------
node_modules, Python virtual environments, build output, caches, and .git are
excluded because they are large and can be recreated. Your source code,
package files, requirements, portal, local JSON data, and database export are
preserved.

Important privacy note
----------------------
The backup may contain .env files, API keys, or Firebase credentials if you add
them later. Keep the backup private. Do not upload it to a public GitHub
repository.

Do not use the backup as a replacement for the working folder. Keep at least
one copy on another drive or in private cloud storage.

