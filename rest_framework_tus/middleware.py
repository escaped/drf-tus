# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64

from django.http.response import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from rest_framework import status

from rest_framework_tus import tus_api_version, constants


class TusMiddleware(MiddlewareMixin):
    REQUIRED_REQUEST_HEADERS = {
        'Tus-Resumable': constants.TUS_RESUMABLE_FIELD_NAME
    }

    def __init__(self, get_response=None):
        super(TusMiddleware, self).__init__(get_response)

    def process_request(self, request):
        for header, field_name in self.REQUIRED_REQUEST_HEADERS.items():
            if header not in request.META.get('headers', {}):
                return HttpResponse('Missing "{}" header.'.format(header), status=status.HTTP_400_BAD_REQUEST)
            else:
                setattr(request, field_name, request.META.get('headers', {})[header])

        # Parse upload length
        self.parse_upload_length(request)

        # Parse upload upload_offset
        self.parse_upload_offset(request)

        # Parse defer upload length
        self.parse_upload_defer_length(request)

        # Parse upload metadata
        self.parse_upload_metadata(request)

    def process_response(self, request, response):
        if 'Tus-Resumable' not in response:
            response['Tus-Resumable'] = tus_api_version

        return response

    @classmethod
    def parse_upload_defer_length(cls, request,):
        upload_defer_length = request.META.get('headers', {}).get('Upload-Defer-Length', None)

        if not upload_defer_length:
            return

        upload_defer_length = int(upload_defer_length)

        if upload_defer_length != 1:
            return HttpResponse('Invalid value for "Upload-Defer-Length" header: {}.'.format(upload_defer_length),
                                status=status.HTTP_400_BAD_REQUEST)

        # Set upload defer length
        setattr(request, constants.UPLOAD_DEFER_LENGTH_FIELD_NAME, upload_defer_length)

    @classmethod
    def parse_upload_offset(cls, request):
        upload_offset = request.META.get('headers', {}).get('Upload-Offset', None)

        if upload_offset is None:
            return

        # Set upload length
        setattr(request, constants.UPLOAD_OFFSET_NAME, int(upload_offset))

    @classmethod
    def parse_upload_length(cls, request):
        upload_length = request.META.get('headers', {}).get('Upload-Length', None)

        if upload_length is None:
            return

        # Set upload length
        setattr(request, constants.UPLOAD_LENGTH_FIELD_NAME, int(upload_length))

    @classmethod
    def parse_upload_metadata(cls, request):
        upload_meta_header = request.META.get('headers', {}).get('Upload-Metadata', None)

        if upload_meta_header is None:
            return

        upload_metadata = {}

        for key_value_pair in upload_meta_header.split(','):
            # Trim whitespace
            key_value_pair = key_value_pair.strip()

            # Split key and value
            key, value = key_value_pair.split(' ')

            # Store data
            upload_metadata[key] = base64.decodebytes(value.encode('utf-8')).decode('ascii')

        # Set upload_metadata
        setattr(request, constants.UPLOAD_METADATA_FIELD_NAME, upload_metadata)
