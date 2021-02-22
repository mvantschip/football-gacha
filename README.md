# How to work with this template:
1) Make a virtual environment and install from requirements.txt using pip (pip install -r requirements.txt)
2) Rename the db folder, to something reflecting your project.
3) change the INSTALLED_APPS, to reflect this name change (i.e. change db to the new folder name)
4) copy the secret_template.json and name it secret.json. Copy it again, name it secret_dev.json
5) Create a postgres database for said project
6) Remember the name of the DB, remember your credentials with which you can log in to your db
7) Change the db_user and db_pw entries in the secret.json and secret_dev.json files
8) Create a new discord bot. Copy the secret, enter it under discord_secret
9) Make sure to enter the channel ids for these parameters in the secret file (from bot_owner_id onward)
10) Make sure that you enter the correct development platform for loading the secret_dev.json. The default setting is "darwin" (which is MacOS). For Windows, change "darwin" to "win32".
11) Make sure you create the tables in your database by running "python manage.py makemigrations" and "python manage.py migrate"
