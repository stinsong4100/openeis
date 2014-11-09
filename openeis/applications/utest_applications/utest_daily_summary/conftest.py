import os
import pytest

from openeis.projects import models
from openeis.applications.utest_applications.conftest import (project,
                                                              create_data_file,
                                                              create_dataset,
                                                              active_user)  

abs_file_dir = os.path.join(os.path.dirname(__file__))

@pytest.fixture
def daily_summary_datafile(project):
    return create_data_file(os.path.join(abs_file_dir, 'daily_summary_data.csv'), 
                            project=project,
                            comments='Daily Summary test data.')
@pytest.fixture
def samenumber_datamap(project):
    return create_datamap(project, "samenumber")

@pytest.fixture
def samenumber_dataset(project, samenumber_datamap, daily_summary_datafile):
    return create_dataset(name='Daily Summary Datamap', project=project, 
                          datamap=samenumber_datamap, 
                          files={'0': daily_summary_datafile})
    
@pytest.fixture
def onetofive_datamap(project):
    return create_datamap(project, "onetofive")

@pytest.fixture
def onetofive_dataset(project, onetofive_datamap, daily_summary_datafile):
    return create_dataset(name='Daily Summary Datamap', project=project, 
                          datamap=onetofive_datamap, 
                          files={'0': daily_summary_datafile})

@pytest.fixture
def missing_numbers_datamap(project):
    return create_datamap(project, "missingandfloats")

@pytest.fixture
def missing_numbers_dataset(project, missing_numbers_datamap, daily_summary_datafile):
    return create_dataset(name='Daily Summary Datamap', project=project, 
                          datamap=missing_numbers_datamap, 
                          files={'0': daily_summary_datafile})

def create_datamap(project, column):
    return models.DataMap.objects.create(project=project, name="Daily Summary Map",
        map={
            
            "sensors": {
                "lbnl/bldg90/WholeBuildingElectricity": {
                    "column": column,
                    "unit":"kilowatt",
                    "type": "WholeBuildingElectricity",
                    "file": "0"
                },
                "lbnl":{
                    "level":"site"
                }
            },
            "files": {
                "0": {
                    "signature": {
                        "headers": [
                            "datetime", 
                            "onetofive", 
                            "withmissing", 
                            "samenumber", 
                            "floats", 
                            "missingandfloats"
                        ]
                    },
                    "timestamp": {
                        "columns": [
                            0
                        ]
                    }
                }
            },
            "version": 1
        })
    
    

#     return models.DataMap.objects.create(project=project, name="Daily Summary Map",
#         map={
#             
#             "sensors": {
#                 "lbnl/bldg90/WholeBuildingElectricity": {
#                     "column": "samenumber",
#                     "unit":"kilowatt",
#                     "type": "WholeBuildingElectricity",
#                     "file": "0"
#                 },
#                 "lbnl":{
#                     "level":"site"
#                 }
#             },
#             "files": {
#                 "0": {
#                     "signature": {
#                         "headers": [
#                             "datetime", 
#                             "onetofive", 
#                             "withmissing", 
#                             "samenumber", 
#                             "floats", 
#                             "missingandfloats"
#                         ]
#                     },
#                     "timestamp": {
#                         "columns": [
#                             0
#                         ]
#                     }
#                 }
#             },
#             "version": 1
#         })