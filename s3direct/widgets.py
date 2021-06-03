from __future__ import unicode_literals

import os
from urllib.parse import urlparse

from django.forms import widgets
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.http import urlunquote_plus
from django.conf import settings

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None


class S3DirectWidget(widgets.TextInput):
    class Media:
        js = ('s3direct/dist/index.js', )
        css = {'all': ('s3direct/dist/index.css', )}

    def __init__(self, *args, **kwargs):
        self.dest = kwargs.pop('dest', None)
        self.use_presigned_url = kwargs.pop('use_presigned_url', None)
        super(S3DirectWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, **kwargs):
        file_url = value or ''
        csrf_cookie_name = getattr(settings, 'CSRF_COOKIE_NAME', 'csrftoken')
        file_name = os.path.basename(urlunquote_plus(file_url))
        if self.use_presigned_url and file_url:
            if isinstance(file_name, tuple):
                file_name = file_name[0]
            s3_key = urlparse(file_url).path.replace(settings.AWS_STORAGE_BUCKET_NAME + "/","")
            # url must be relative
            if s3_key[0] == "/":
                s3_key = s3_key[1:]
            # generate a presigned URL for the asset
            s3_client = boto3.client('s3', "us-east-1")
            try:
                file_url = s3_client.generate_presigned_url('get_object',
                                                            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,'Key': s3_key},
                                                            ExpiresIn=3600)
            except ClientError as e:
                pass

        ctx = {
            'policy_url': reverse('s3direct'),
            'signing_url': reverse('s3direct-signing'),
            'dest': self.dest,
            'name': name,
            'csrf_cookie_name': csrf_cookie_name,
            'file_url': file_url,
            'file_name': file_name,
        }

        return mark_safe(
            render_to_string(os.path.join('s3direct', 's3direct-widget.tpl'),
                             ctx))
