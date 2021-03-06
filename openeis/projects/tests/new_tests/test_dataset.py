
import datetime
from collections import namedtuple

from django.utils.timezone import utc
import pytest
from rest_framework.test import force_authenticate, APIRequestFactory, APIClient
from rest_framework import status

from openeis.projects import views, conf

from .conftest import detail_view


pytestmark = pytest.mark.django_db


Summary = namedtuple('Summary', 'count header first_row last_row')

def summarize(data):
    '''Iterate over a dataset and summarize what's there.

    count is the number of rows, minus the header, in the data set.
    header is the first row, which should be the header.
    first_row is the first row of data in the data set.
    last_row is the last row of data in the data set.
    '''
    it = iter(data)
    header, first_row, last_row = None, None, None
    count = 0
    try:
        header = next(it)
        first_row = last_row = next(it)
        count = 1
        for last_row in it:
            count += 1
    except StopIteration:
        pass
    return Summary(count, header, first_row, last_row)


def test_dataset_merge(mixed_dataset):
    '''Test the merge method of the SensorIngest model.'''

    dataset = mixed_dataset
    # All data includes count of all records for both sensors plus header
    total = sum(sensor.data.filter(ingest=dataset).count()
                for sensor in dataset.map.sensors.all())
    rows = list(dataset.merge())
    assert len(rows) == total + 1
    assert rows[0][0] == 'time'

    # Only merge last day -- includes 24 records per sensor plus header
    start = datetime.datetime(2012, 2, 29, 0, tzinfo=utc)
    summary = summarize(dataset.merge(start=start))
    assert summary.count == 48
    assert summary.header == rows[0]   # Check that header rows match
    assert summary.first_row[0] == start
    assert summary.first_row[1] is None   # Check that empty values are empty
    assert summary.first_row[2] is not None
    assert summary.last_row == rows[-1]

    # Merge up to last day
    end = datetime.datetime(2012, 2, 29, 0, tzinfo=utc)
    summary = summarize(dataset.merge(end=end))
    assert summary.header == rows[0]   # Check that header rows match
    assert summary.count == total - 48
    assert summary.first_row == rows[1]
    assert summary.last_row == rows[-49]
    assert summary.last_row[0] < end

    # Skip first 1000 records
    summary = summarize(dataset.merge(start=1000))
    assert summary.header == rows[0]   # Check that header rows match
    assert summary.count == total - 1000
    assert summary.first_row == rows[1001]
    assert summary.last_row == rows[-1]

    # Skip last 1000 records
    summary = summarize(dataset.merge(end=total-1000))
    assert summary.header == rows[0]   # Check that header rows match
    assert summary.count == total - 1000
    assert summary.first_row == rows[1]
    assert summary.last_row == rows[total-1000]

    # Merge a single day
    start = datetime.datetime(2012, 2, 9, 0, tzinfo=utc)
    end = datetime.datetime(2012, 2, 10, 0, tzinfo=utc)
    summary = summarize(dataset.merge(start=start, end=end))
    assert summary.header == rows[0]   # Check that header rows match
    assert summary.count == 48
    assert summary.first_row == rows[385]
    assert summary.first_row[0] == start
    assert summary.last_row == rows[432]
    assert summary.last_row[0] < end

    # Merge first 10 records of the day
    summary = summarize(dataset.merge(start=start, end=10))
    assert summary.header == rows[0]   # Check that header rows match
    assert summary.count == 10
    assert summary.first_row == rows[385]
    assert summary.first_row[0] == start
    assert summary.last_row == rows[394]

    # Merge a chunk of records from the middle
    summary = summarize(dataset.merge(start=100, end=100))
    assert summary.header == rows[0]   # Check that header rows match
    assert summary.count == 100
    assert summary.first_row == rows[101]
    assert summary.last_row == rows[200]

    # Merge a chunk of records from the middle
    summary = summarize(dataset.merge(include_header=False))
    assert summary.header == rows[1]   # Check that header rows match
    assert summary.count == len(rows) - 2
    assert summary.first_row == rows[2]
    assert summary.last_row == rows[-1]


def test_dataset_download_url(active_user, mixed_dataset):
    '''Tests download_url transformation.'''

    # Check that download URL is absolute
    client = APIClient()
    client.force_authenticate(user=active_user)
    dataset = mixed_dataset
    url = '/api/datasets/{}'.format(dataset.pk)
    response = client.get(url)
    assert response.data['download_url'] == 'http://testserver{}/download'.format(url)


def test_dataset_download_viewset(active_user, mixed_dataset):
    '''Tests the download method of the DataSetViewSet.'''

    rf = APIRequestFactory()
    dataset = mixed_dataset
    url = '/api/datasets/{}/download'.format(dataset.pk)
    # All data includes count of all records for both sensors plus header
    total = sum(sensor.data.filter(ingest=dataset).count()
                for sensor in dataset.map.sensors.all())
    rows = list(dataset.merge())
    assert len(rows) == total + 1
    assert rows[0][0] == 'time'

    # Check downloading all data
    request = rf.get(url)
    force_authenticate(request, active_user)
    view = views.DataSetViewSet.as_view({'get': 'download'})
    response = view(request, pk=dataset.pk)
    summary = summarize(response.data)
    assert summary.count == total
    assert summary.header == rows[0]
    assert summary.first_row == rows[1]
    assert summary.last_row == rows[-1]

    # Check start date parsing works
    request = rf.get(url, {'start': '2012-02-29 00:00:00+00:00'})
    force_authenticate(request, active_user)
    response = view(request, pk=dataset.pk)
    summary = summarize(response.data)
    assert summary.count == 48
    assert summary.header == rows[0]
    assert summary.first_row == rows[-48]
    assert summary.last_row == rows[-1]

    # Check end date parsing works
    request = rf.get(url, {'end': '2012-02-29 00:00:00+00:00'})
    force_authenticate(request, active_user)
    response = view(request, pk=dataset.pk)
    summary = summarize(response.data)
    assert summary.count == len(rows) - 49
    assert summary.header == rows[0]
    assert summary.first_row == rows[1]
    assert summary.last_row == rows[-49]

    # Check date chunking works
    request = rf.get(url, {'start': '2012-02-28 00:00:00+00:00',
                           'end': '2012-02-29 00:00:00+00:00'})
    force_authenticate(request, active_user)
    response = view(request, pk=dataset.pk)
    summary = summarize(response.data)
    assert summary.count == 48
    assert summary.header == rows[0]
    assert summary.first_row == rows[-96]
    assert summary.last_row == rows[-49]

    # Check integer chunking works
    request = rf.get(url, {'start': '100', 'end': '100'})
    force_authenticate(request, active_user)
    response = view(request, pk=dataset.pk)
    summary = summarize(response.data)
    assert summary.count == 100
    assert summary.header == rows[0]
    assert summary.first_row == rows[101]
    assert summary.last_row == rows[200]

    # Check for bad start and end
    request = rf.get(url, {'start': 'abc', 'end': 'xyz'})
    force_authenticate(request, active_user)
    response = view(request, pk=dataset.pk)
    summary = summarize(response.data)
    assert summary.count == len(rows) - 1
    assert summary.header == rows[0]
    assert summary.first_row == rows[1]
    assert summary.last_row == rows[-1]

    # Check for bad start and end
    request = rf.get(url, {'start': '-1', 'end': '-1'})
    force_authenticate(request, active_user)
    response = view(request, pk=dataset.pk)
    summary = summarize(response.data)
    assert summary.count == 0
    assert summary.header == rows[0]
    assert summary.first_row is None
    assert summary.last_row is None


def test_dataset_download_api(active_user, mixed_dataset):
    '''Tests the content negotiation of the dataset download API.'''

    client = APIClient()
    client.force_authenticate(user=active_user)
    dataset = mixed_dataset
    url = '/api/datasets/{}/download'.format(dataset.pk)
    response = client.get(url)
    assert isinstance(response, views.renderers.StreamingCSVResponse)
    response = client.get(url, {'format': 'csv'})
    assert isinstance(response, views.renderers.StreamingCSVResponse)
    response = client.get(url, {'format': 'json'})
    assert isinstance(response, views.Response)


def test_dataset_preview(active_user, mixed_datamap,
        datafile_1month, datafile_1month_offset):
    '''Tests previewing dataset creation without saving the data.'''

    rf = APIRequestFactory()
    post = lambda data: rf.post('/api/datasets/preview', data, format='json')
    expected_response = {
        'cols': [
            'time',
            'Test/WholeBuildingPower',
            'Test/OutdoorAirTemperature'
        ],
        'rows': [
            [datetime.datetime(2012, 2, 1, 0, 0, tzinfo=utc), 108.52, None],
            [datetime.datetime(2012, 2, 1, 0, 30, tzinfo=utc), None, 45.67],
            [datetime.datetime(2012, 2, 1, 1, 0, tzinfo=utc), 111.86, None],
            [datetime.datetime(2012, 2, 1, 1, 30, tzinfo=utc), None, 46.18],
            [datetime.datetime(2012, 2, 1, 2, 0, tzinfo=utc), 113.87, None],
            [datetime.datetime(2012, 2, 1, 2, 30, tzinfo=utc), None, 47.08],
            [datetime.datetime(2012, 2, 1, 3, 0, tzinfo=utc), 114.24, None],
            [datetime.datetime(2012, 2, 1, 3, 30, tzinfo=utc), None, 47.08],
            [datetime.datetime(2012, 2, 1, 4, 0, tzinfo=utc), 139.99, None],
            [datetime.datetime(2012, 2, 1, 4, 30, tzinfo=utc), None, 47.61],
            [datetime.datetime(2012, 2, 1, 5, 0, tzinfo=utc), 145.86, None],
            [datetime.datetime(2012, 2, 1, 5, 30, tzinfo=utc), None, 47.91],
            [datetime.datetime(2012, 2, 1, 6, 0, tzinfo=utc), 153.62, None],
            [datetime.datetime(2012, 2, 1, 6, 30, tzinfo=utc), None, 48.23],
            [datetime.datetime(2012, 2, 1, 7, 0, tzinfo=utc), 167.61, None],
            [datetime.datetime(2012, 2, 1, 7, 30, tzinfo=utc), None, 48.45],
            [datetime.datetime(2012, 2, 1, 8, 0, tzinfo=utc), 187.12, None],
            [datetime.datetime(2012, 2, 1, 8, 30, tzinfo=utc), None, 49.47],
            [datetime.datetime(2012, 2, 1, 9, 0, tzinfo=utc), 204.19, None],
            [datetime.datetime(2012, 2, 1, 9, 30, tzinfo=utc), None, 50.78]
        ]
    }
    
    # Check using numeric map value of existing map
    request = post({'map': mixed_datamap.pk, 'rows': 20,
            'files': [{'name': '0', 'file': datafile_1month.pk},
                      {'name': '1', 'file': datafile_1month_offset.pk}]})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response
    assert len(response.data['cols']) == 3
    assert len(response.data['rows']) == 20
    
    # Check using short map with id of existing map
    request = post({'map': {'id': mixed_datamap.pk}, 'rows': 20,
            'files': [{'name': '0', 'file': datafile_1month.pk},
                      {'name': '1', 'file': datafile_1month_offset.pk}]})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response
    assert len(response.data['cols']) == 3
    assert len(response.data['rows']) == 20
    assert 'extra_rows' not in response.data
    
    # Check using full map to preview unsaved datamap
    request = post({'map': mixed_datamap.map, 'rows': 20,
            'files': [{'name': '0', 'file': datafile_1month.pk},
                      {'name': '1', 'file': datafile_1month_offset.pk}]})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response
    assert len(response.data['cols']) == 3
    assert len(response.data['rows']) == 20
    assert 'extra_rows' not in response.data
    
    # Check alternate file specification using map instead of list
    request = post({'map': mixed_datamap.map, 'rows': 20,
            'files': {'0': datafile_1month.pk, '1': datafile_1month_offset.pk}})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_response
    assert len(response.data['cols']) == 3
    assert len(response.data['rows']) == 20
    assert 'extra_rows' not in response.data
    
    # Check requesting fewer rows
    request = post({'map': mixed_datamap.pk, 'rows': 10,
            'files': {'0': datafile_1month.pk, '1': datafile_1month_offset.pk}})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['rows'] == expected_response['rows'][:10]
    assert len(response.data['cols']) == 3
    assert len(response.data['rows']) == 10
    assert 'extra_rows' not in response.data
    
    # Check requesting zero rows
    request = post({'map': mixed_datamap.pk, 'rows': 0,
            'files': {'0': datafile_1month.pk, '1': datafile_1month_offset.pk}})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['cols']) == 3
    assert len(response.data['rows']) == 0
    assert 'extra_rows' in response.data
    assert response.data['extra_rows'] == expected_response['rows'][:2]
    
    # Check requesting one row
    request = post({'map': mixed_datamap.pk, 'rows': 1,
            'files': {'0': datafile_1month.pk, '1': datafile_1month_offset.pk}})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['cols']) == 3
    assert len(response.data['rows']) == 1
    assert 'extra_rows' in response.data
    assert response.data['rows'] == expected_response['rows'][:1]
    assert response.data['extra_rows'] == expected_response['rows'][1:2]
    
    # Check requesting default rows
    request = post({'map': mixed_datamap.pk,
            'files': {'0': datafile_1month.pk, '1': datafile_1month_offset.pk}})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['cols']) == 3
    assert len(response.data['rows']) == conf.settings.FILE_HEAD_ROWS_DEFAULT
    assert 'extra_rows' not in response.data
    
    # Check requesting too many rows
    request = post({'map': mixed_datamap.pk, 'rows': 80000,
            'files': {'0': datafile_1month.pk, '1': datafile_1month_offset.pk}})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['cols']) == 3
    assert len(response.data['rows']) == conf.settings.FILE_HEAD_ROWS_MAX
     
    # Check invalid datamap ID
    request = post({'map': 2000, 'files': {'0': datafile_1month.pk}})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data == {'detail': 'Not found'}
     
    # Check invalid datamap
    request = post({'map': {'extra': {'bad': 'robot'}},
        'files': {'0': datafile_1month.pk}})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {'map': ["'version' is a required property"]}
    
    # Check request with invalid file id
    request = post({'map': mixed_datamap.pk,
            'files': {'0': 2000, '1': datafile_1month_offset.pk}})
    force_authenticate(request, active_user)
    view = views.DataSetPreviewViewSet.as_view({'post': 'preview'})
    response = view(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response.data['files'].sort(key=lambda x: x.keys())
    assert response.data == {'files': [{}, {'file': ["Invalid pk '2000' - object does not exist."]}]}
