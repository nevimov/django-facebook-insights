from django.db import models

from facebook_insights.models import Insights

__all__ = ['PostInsights', 'PageInsights', 'PostInsightsWithoutGraphID',
           'Post']


class PostInsights(Insights):
    METRICS = [
        'post_impressions',
        'post_impressions_fan',
        'post_impressions_unique',
        'post_interests_consumptions_unique',
        'post_interests_impressions',
        'post_stories',
        'post_stories_by_action_type',
        'post_storytellers',
    ]
    graph_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="The page post ID on Facebook",
    )
    impressions = models.PositiveIntegerField(null=True)
    impressions_fan = models.PositiveIntegerField(null=True)
    impressions_unique = models.PositiveIntegerField(null=True)
    interests_consumptions_unique = models.CharField(null=True, max_length=80)
    interests_impressions = models.CharField(null=True, max_length=80)
    stories = models.PositiveIntegerField(null=True)
    stories_by_action_type = models.CharField(null=True, max_length=80)
    storytellers = models.PositiveIntegerField(null=True)


class PageInsights(Insights):
    METRICS = [
        'page_engaged_users',
        'page_impressions',
        'page_impressions_unique',
        'page_posts_impressions',
    ]
    graph_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="The page post ID on Facebook",
    )
    engaged_users = models.CharField(null=True, max_length=80)
    impressions = models.CharField(null=True, max_length=80)
    impressions_unique = models.CharField(null=True, max_length=80)
    posts_impressions = models.CharField(null=True, max_length=80)


class Post(models.Model):
    graph_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="The page post ID on Facebook",
    )


class PostInsightsWithoutGraphID(Insights):
    RELATED_OBJECT_FIELD = 'post'
    post = models.OneToOneField(Post)
