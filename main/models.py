from django.db import models
# TODO add readable field names to fields


class Contest(models.Model):
    name = models.CharField(max_length=255)
    duration = models.IntegerField
    start_time = models.DateTimeField
    description = models.TextField
    freezing_time = models.IntegerField
    is_school = models.BooleanField
    is_admin = models.BooleanField
    is_training = models.BooleanField


class Notification(models.Model):
    description = models.TextField
    contest = models.ForeignKey(Contest)
    visible = models.BooleanField


class Problem(models.Model):
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    description = models.TextField
    time_limit = models.IntegerField
    memory_limit = models.IntegerField
    checker = models.CharField(max_length=255)
    mask_in = models.CharField(max_length=255)
    mask_out = models.CharField(max_length=255)
    tests_count = models.IntegerField  # TODO delete this field as soon as can
    analysis = models.IntegerField
    author = models.CharField(max_length=64)
    developer = models.CharField(max_length=64)
    origin = models.CharField(max_length=128)
    input_file = models.CharField(max_length=16)
    output_file = models.CharField(max_length=16)
    input_specification = models.TextField
    output_specification = models.TextField
    samples = models.TextField
    explanations = models.TextField
    notes = models.TextField


class ProblemInContest(models.Model):
    contest = models.ForeignKey(Contest)
    problem = models.ForeignKey(Problem)
    number = models.IntegerField
    score = models.IntegerField


class Compilers(models.Model):
    name = models.CharField(max_length=255)
    extension = models.CharField(max_length=255)
    compile_string = models.CharField(max_length=255)