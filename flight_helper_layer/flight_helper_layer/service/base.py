from abc import ABC, abstractmethod
from helperlayer import JsonTransform


class FlightProcessor(ABC):
    def __init__(self):
        self._vendor = None  # Protected attribute

    @abstractmethod
    def _lfs_transform_data(self):
        pass

    @abstractmethod
    def _get_mapping(self):
        pass

    def _lfs_convert_data_using_mapping(self, source_data, data_mapping, parent_data=None):
        return JsonTransform().transform_data(source_data, data_mapping, parent_data)
