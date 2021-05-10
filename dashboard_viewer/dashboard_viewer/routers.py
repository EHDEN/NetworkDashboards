class AchillesRouter:
    """
    Defines:
        - from/to which databases the models will be read/written
        - the allowed relations between objects
        - what migrations should be applied to which database

    Models related to the uploader app will be used only on the
     achilles database. The rest will be stored on the default database
    """

    achilles_apps = ["uploader", "materialized_queries_manager", "updates"]
    achilles_db = "achilles"

    def db_for_read(self, model, **_):
        if model._meta.app_label in self.achilles_apps:
            return self.achilles_db
        return None

    def db_for_write(self, model, **_):
        if model._meta.app_label in self.achilles_apps:
            return self.achilles_db
        return None

    def allow_relation(self, obj1, obj2, **_):
        if (
            obj1._meta.app_label in self.achilles_apps
            or obj2._meta.app_label in self.achilles_apps
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, **_):
        if db == self.achilles_db:
            result = app_label in self.achilles_apps
            return result
        if app_label in self.achilles_apps:
            result = db == self.achilles_db
            return result
        return None
