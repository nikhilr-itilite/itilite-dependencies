from typing import Union
from flight_helper_layer.service.json.json_factory import JSONFactory
from flight_helper_layer.service.xml.xml_factory import XMLFactory
from flight_helper_layer.service.enums import ApiFormat


class FlightFactory:
    @staticmethod
    def get_type(file_type: str) -> Union[JSONFactory, XMLFactory]:
        if file_type == ApiFormat.JSON.value:
            return JSONFactory()
        elif file_type == ApiFormat.XML.value:
            return XMLFactory()
        else:
            raise ValueError("Unknown file type")
