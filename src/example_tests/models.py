from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify


class TestQuestionnaire(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    questions_per_page = models.IntegerField()

    class Meta:
        verbose_name = "test questionnaire"
        verbose_name_plural = "test questionnaires"

    def get_absolute_url(self):
        return reverse('example_tests:q-detail', args=[str(self.pk)])

    def set_slug_from_name(self):
        self.slug = slugify(self.name)

    def __str__(self):
        return self.name
