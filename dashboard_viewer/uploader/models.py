from django.db import models

class AchillesResults(models.Model):
	class Meta:
		db_table = "AchillesResults"

	source		= models.TextField()
	analysis_id	= models.BigIntegerField()
	stratum_1	= models.TextField()
	stratum_2	= models.TextField()
	stratum_3	= models.TextField()
	stratum_4	= models.TextField()
	stratum_5	= models.TextField()
	count_value	= models.BigIntegerField()

class Uploads(models.Model):
	pass