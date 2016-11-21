========================
django-facebook-insights
========================

Collect and store `Facebook Insights`_ metrics using Django models.

This app provides a flexible abstract model with method `fetch()`. It gets all
required metrics with a single `batch request`_ to Graph API and puts them into
your child model's fields.

**Requirements**:

* Django 1.7 to 1.10 on Python 2.7
* Django 1.8 to 1.10 on Python 3.4 and 3.5
* facebook-sdk 1.0.0+

.. contents::
   :depth: 1
   :backlinks: top


Installation
------------

Install the app with pip::

    $ pip install django-facebook-insights

Add `'facebook_insights'` to your `INSTALLED_APPS` setting::

    INSTALLED_APPS = [
        ...
        'facebook_insights',
    ]

Finally, provide a valid access token with the 'read_insights' permission using
setting `FACEBOOK_INSIGHTS_ACCESS_TOKEN`.


Usage example
-------------

In the simplest case, all you need to do is to write code similar to the
one below::

    from django.db import models
    from facebook_insights.models import Insights


    # Inherit from the abstract 'Insights' model
    class PostInsights(Insights):
        # List metrics you're intrested in
        METRICS = [
            'post_impressions',
            'post_impressions_unique',
            'post_stories',
            'post_stories_by_action_type',
        ]
        # Define field 'graph_id' to hold the Facebook ids of objects
        graph_id = models.CharField(max_length=100)
        # Define fields to store the metrics
        impressions = models.PositiveIntegerField()
        impressions_unique = models.PositiveIntegerField()
        stories = models.PositiveIntegerField()
        stories_by_action_type = models.CharField(max_length=100)

.. note::
    If you want to use a different name for the graph id field, change
    attribute GRAPH_ID_FIELD to the desired value.

Now, you can instantiate the model and call fetch() to get the metrics from
Facebook's servers::

    >>> post_insights = PostInsights(graph_id=your_post_id)
    >>> post_insights.fetch()
    >>> post_insights.impressions
    1000
    >>> post_insights.impressions_unique
    200
    >>> post_insights.stories
    100
    >>> post_insights.stories_by_action_type
    '{"like": 40, "share": 30, "comment": 30}'


Mapping metrics to fields
-------------------------

To figure out which metrics belong to which fields, the app uses the following
simple algorithm:

* Take the metric name as the base name.

* Remove the object type prefix (``'post_', 'page_' or 'domain_'``),
  if attribute REMOVE_PREFIX is set to True (the default).
  The prefix is removed, so we can, for instance, access the
  'post_impressions' metric as `post_insights.impressions` instead of
  `post_insights.post_impressions`.

.. note::

    The full list of *metrics* with their *periods* can be found in Graph API
    Reference on `Object Insights`_.

If you want to use a more complex algorithm, you need to override the
`get_field_name()` method.


Extracting field values
-----------------------

Values associated with page metrics are quite complex. They are available for
several periods (e.g. day, week, 28 days) and include data for 3 consecutive
days. By contrast, values of most of post metrics are available only for one
period (lifetime) and represent the current state of things.

The extraction of metric values is the responsibility of the
`get_field_value()` method. The default implementation works as follows:

* If a metric has several periods, return the dictionary of mappings between
  the periods and the last available values for these periods serialized into
  JSON, for example, `'{"day": 10, "week": 70, "days_28": 300"}'`. The data
  for previous days are discarded.
* If a metric is provided only for a single period, then simply return the
  value (serialize, if it's not a number).

Feel free to override the method, if you want something else.


Getting object_id from a related object
---------------------------------------

In case you already have a model representing a Facebook page or post, you will
likely want to get the graph ids from instances of this model. To do this,
all you need is to set attribute RELATED_OBJECT_FIELD to the name of the field
referencing the related object::

    class Page(models.Model):
        graph_id = models.CharField(
            max_length=100,
            primary_key=True,
            help_text="The page's ID on Facebook",
        )


    class PageInsights(Insights):
        RELATED_OBJECT_FIELD = 'page'
        METRICS = [ ... ]
        page = models.OneToOneField(
            Page,
            primary_key=True,
            related_name='insights',
        )
        ...


Reporting bugs
--------------

If you've found a bug:

* Check to see if there's an existing issue/pull request for the bug.

  | PR:     https://github.com/nevimov/django-facebook-insights/pulls
  | Issues: https://github.com/nevimov/django-facebook-insights/issues

* If there isn't one, file an issue. A bug report should include:

  * a description of the problem
  * instructions on how to recreate the bug
  * versions of your Python interpreter and Django


Contributing code
-----------------

* Fork the project on GitHub to your account.

* Clone the repository::

    $ git clone https://github.com/nevimov/django-facebook-insights

* Optionally, create and activate a virtual environment::

    $ virtualenv venv
    $ source venv/bin/activate

* In directory 'tests' create a file named 'secret.py'. In this file, set
   the `FACEBOOK_INSIGHTS_ACCESS_TOKEN` setting'.  Alternatively, define an
   environment variable with the same name.

* If you use Python 2, you'll need to install *mock*::

    $ pip install mock

* Run tests to ensure everything is OK::

    $ python runtests.py

  You can use *-h* or *--help* to see options available to the script.

* Create a topic branch and commit your changes there.

* Push the branch up to GitHub.

* Create a new pull request.


.. _Object Insights:
.. _Facebook Insights: https://developers.facebook.com/docs/graph-api/reference/v2.8/insights
.. _batch request: https://developers.facebook.com/docs/graph-api/making-multiple-requests
