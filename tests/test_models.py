"""Tests for the 'facebook_insights.models' module."""
import json

from django.test import TestCase
from facebook import GraphAPIError

from facebook_insights.models import Insights
from facebook_insights.metrics import Metric
from tests.models import (PageInsights, PostInsights, Post,
                          PostInsightsWithoutGraphID)

TEST_PAGE_ID = '327730534261730'
TEST_POST_ID = '327730534261730_327732570928193'


class TestInsights(TestCase):
    """Tests for the 'Insights' model."""

    def setUp(self):
        self.post_insights = PostInsights(graph_id=TEST_POST_ID)
        self.page_insights = PageInsights(graph_id=TEST_PAGE_ID)

    def test_get_object_id_from_instance(self):
        """get_object_id() should return the value of a field specified by
        GRAPH_ID_FIELD.
        """
        post_insights = self.post_insights
        self.assertEqual(post_insights.GRAPH_ID_FIELD, 'graph_id')
        self.assertEqual(post_insights.graph_id, TEST_POST_ID)
        self.assertEqual(post_insights.get_graph_id(), TEST_POST_ID)

    def test_get_object_id_from_related_object(self):
        """get_object_id() should return the value of a field specified by
        GRAPH_ID_FIELD. If the field isn't found on the instance, it's searched
        on a related object specified by RELATED_OBJECT_FIELD.
        """
        post = Post(graph_id='111111111_22222222')
        post.save()
        post_insights = PostInsightsWithoutGraphID(post=post)
        self.assertEqual(post_insights.RELATED_OBJECT_FIELD, 'post')
        self.assertEqual(post_insights.get_graph_id(), '111111111_22222222')

    def test_get_field_name(self):
        post_insights = self.post_insights
        get_field_name = self.post_insights.get_field_name
        self.assertTrue(post_insights.REMOVE_PREFIX)
        metric = Metric(name='post_stories', values={'foo': 'bar'})
        self.assertEqual(get_field_name(metric), 'stories')
        metric.name = 'domain_feed_clicks'
        self.assertEqual(get_field_name(metric), 'feed_clicks')
        metric.name = 'page_engaged_users'
        self.assertEqual(get_field_name(metric), 'engaged_users')
        metric.name = 'page_posts_impressions'
        self.assertEqual(get_field_name(metric), 'posts_impressions')
        self.post_insights.REMOVE_PREFIX = False
        metric.name = 'post_stories'
        self.assertEqual(get_field_name(metric), 'post_stories')
        metric.name = 'domain_feed_clicks'
        self.assertEqual(get_field_name(metric), 'domain_feed_clicks')
        metric.name = 'page_engaged_users'
        self.assertEqual(get_field_name(metric), 'page_engaged_users')
        metric.name = 'page_posts_impressions'
        self.assertEqual(get_field_name(metric), 'page_posts_impressions')

    def test_get_field_value(self):
        get_field_value = self.post_insights.get_field_value
        # If a metric has only one value, it should be extracted
        metric = Metric(
            name='post_impressions',
            values={'lifetime': [{ 'value': 1 }]}
        )
        # If the value is not a number, it should be serialized into JSON
        self.assertEqual(get_field_value(metric), 1)
        metric = Metric(
            name='post_interests_impressions',
            values={'lifetime': [{ 'value': {} }]}
        )
        self.assertEqual(get_field_value(metric), '{}')
        values = {
            'day': [
                {'end_time': '2016-11-15T08:00:00+0000', 'value': 0},
                {'end_time': '2016-11-16T08:00:00+0000', 'value': 1},
                {'end_time': '2016-11-17T08:00:00+0000', 'value': 2},
            ],
            'week': [
                {'end_time': '2016-11-15T08:00:00+0000', 'value': 10},
                {'end_time': '2016-11-16T08:00:00+0000', 'value': 11},
                {'end_time': '2016-11-17T08:00:00+0000', 'value': 12},
            ],
            'days_28': [
                {'end_time': '2016-11-15T08:00:00+0000', 'value': 100},
                {'end_time': '2016-11-16T08:00:00+0000', 'value': 101},
                {'end_time': '2016-11-17T08:00:00+0000', 'value': 102},
            ],
        }
        metric = Metric(name='post_engaged_users', values=values)
        self.assertJSONEqual(
            get_field_value(metric),
            '{"day": 2, "week": 12, "days_28": 102}'
        )

    def test_fetch_post_insights(self):
        """Test method fetch() by fetching some post metrics."""
        post_insights = self.post_insights
        post_insights.fetch()
        # Check that the instance can be saved to the database and all
        # fields hold the values we expect.
        post_insights.save()
        post_insights = PostInsights.objects.get(graph_id=TEST_POST_ID)
        self.assertIs(type(post_insights.impressions), int)
        self.assertIs(type(post_insights.impressions_fan), int)
        self.assertIs(type(post_insights.impressions_unique), int)
        self.assertIs(type(post_insights.stories), int)
        self.assertIs(type(post_insights.storytellers), int)
        # These fields are expected to be valid JSON objects
        self.assertIs(
            type(json.loads(post_insights.interests_consumptions_unique)),
            dict
        )
        self.assertIs(
            type(json.loads(post_insights.interests_impressions)),
            dict
        )
        self.assertIs(
            type(json.loads(post_insights.stories_by_action_type)),
            dict
        )

    def test_fetch_page_insights(self):
        """Test method fetch() by fetching some page metrics."""
        page_insights = self.page_insights
        page_insights.fetch()
        # Check that the instance can be saved to the database and all
        # fields hold the values we expect.
        page_insights.save()
        page_insights = PageInsights.objects.get(graph_id=TEST_PAGE_ID)
        # These fields are expected to be valid JSON objects
        self.assertIs(
            type(json.loads(page_insights.engaged_users)),
            dict
        )
        self.assertIs(
            type(json.loads(page_insights.impressions)),
            dict
        )
        self.assertIs(
            type(json.loads(page_insights.impressions_unique)),
            dict
        )
        self.assertIs(
            type(json.loads(page_insights.posts_impressions)),
            dict
        )

    def test_fetch_subset_of_metrics(self):
        """The fetch() method should accept argument 'metrics', which allows
        to fetch only a subset of object metrics.
        """
        post_insights = self.post_insights
        self.assertIsNone(post_insights.impressions)
        self.assertIsNone(post_insights.impressions_fan)
        self.assertIsNone(post_insights.impressions_unique)
        post_insights.fetch(metrics=['post_impressions',
                                     'post_impressions_fan'])
        self.assertTrue(type(post_insights.impressions), int)
        self.assertTrue(type(post_insights.impressions_fan), int)
        self.assertIsNone(post_insights.impressions_unique)

    def test_raises_if_model_does_not_define_field_for_metric(self):
        """If a child of the Insights model doesn't define a field to store
        a metric, then fetch() should raise an appropriate exception.
        """
        try:  # Python 3.2+
            assertRaisesRegex = self.assertRaisesRegex
        except AttributeError:
            assertRaisesRegex = self.assertRaisesRegexp
        page_insights = self.page_insights
        # The model doesn't have the field below
        page_insights.METRICS = ['page_posts_impressions_viral']
        with assertRaisesRegex(AttributeError, 'page_posts_impressions_viral'):
            page_insights.fetch()

    def test_instance_string_representation(self):
        post_insights = self.post_insights
        page_insights = self.page_insights
        self.assertEqual(
            str(page_insights),
            '<PageInsights: {}>'.format(page_insights.graph_id)
        )
        self.assertEqual(
            repr(page_insights),
            '<PageInsights: {}>'.format(page_insights.pk)
        )
        self.assertEqual(
            str(post_insights),
            '<PostInsights: {}>'.format(post_insights.graph_id)
        )
        self.assertEqual(
            repr(post_insights),
            '<PostInsights: {}>'.format(post_insights.pk)
        )
