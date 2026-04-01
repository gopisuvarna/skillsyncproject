'''It tells Django:
“This is an app. Here is its name, settings, and configuration.”'''

from django.apps import AppConfig

#You are creating a configuration class for your app. django reads when project starts
class DocumentsConfig(AppConfig):
    #What type of primary key Django should use by default.
    # big auto field, It is an auto-increment integer field.
    default_auto_field = 'django.db.models.BigAutoField'
    #Where this app is located in Python path.
    name = 'apps.documents'
    #The internal short name of the app. so the table name becomes documents_document 
    label = 'documents'


