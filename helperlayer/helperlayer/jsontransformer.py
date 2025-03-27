import traceback

from opensearchlogger.logging import logger


class JsonTransform:
    def __init__(self):
        self.unique_ids = set()
        self.cache_objs = {}

    def append(self, action_dict, value, source_data):
        """
        Appends the data.
        """
        try:
            value_type = action_dict.get("value_type")
            return_value = None
            if value_type == "const" or not value_type:
                return_value = value + action_dict.get("value", "")
            elif value_type == "var":
                return_value = value
                field_paths = action_dict.get("field_paths", "").split(",")
                for field_path in field_paths:
                    return_value += self.get_ele_from_path(source_data, field_path.split("."))

            return return_value or value
        except Exception:
            logger.warn(f"Error while performing prepend. error: {traceback.format_exc()}")

    def add(self, action_dict, value, source_data):
        """
        Fetches the field(s) data from source_data and Executed add functionality.
        :return: sum value
        """
        try:
            field_paths = action_dict.get("field_paths", "")
            if isinstance(field_paths, str):
                field_paths = field_paths.split(",")
            if not isinstance(field_paths, list):
                logger.warn(f"field_paths {field_paths} should either be a list or comma separated string.")
                return "Invalid Mapping."

            for field_path in field_paths:
                value += self.get_ele_from_path(source_data, field_path.split("."))

            return value
        except Exception:
            logger.warn(f"Could not perform action: add on value: {value}, error: {traceback.format_exc()}")

    def capitalise(self, action_dict, value, source_data):
        """
        Capitalise a string.
        """
        if not isinstance(value, str):
            logger.warn(f"Action capitalise can not be performed on {value}")
            return value
        return value.title()

    def divide(self, action_dict, value, source_data):
        """
        Divide functionality.
        """
        pass

    def prepend(self, action_dict, value, source_data):
        """
        Prepend either a static or variable text to the provided value.
        """
        try:
            value_type = action_dict.get("value_type")
            return_value = None
            if value_type == "const" or not value_type:
                return_value = action_dict.get("value", "") + value
            elif value_type == "var":
                return_value = ""
                field_paths = action_dict.get("field_paths", "").split(",")
                for field_path in field_paths:
                    return_value += self.get_ele_from_path(source_data, field_path.split("."))
                return_value += value

            return return_value or value
        except Exception:
            logger.warn(f"Error while performing prepend. error: {traceback.format_exc()}")

    def multiply(self, action_dict, value, source_data):
        """
        Multiply functionality.
        """
        pass

    def value_in(self, action_dict, value, source_data):
        """
        Checks whether provided value is in an iterable. the iterable could either be static or dynamic.
        """
        value_type = action_dict.get("value_type")
        if value_type == "const" or not value_type:
            values = action_dict.get("values")
            if isinstance(values, str):
                values = values.split(",")
            if isinstance(value, list):
                return any(val in values for val in value)
            return value in values
        elif value_type == "var":
            field_paths = action_dict.get("field_paths", "").split(",")
            for field_path in field_paths:
                values = self.get_ele_from_path(source_data, field_path.split("."))
                if value in values:
                    return True
        return False

    def extract_index_data(self, action_dict, value, source_data):
        """
        return the index level data
        """
        try:
            return value[action_dict["index"]]
        except IndexError:
            logger.warn(f"Index: {action_dict['index']} is out of range")
        except Exception:
            logger.warn(f"Error while doing an extract: error: {traceback.format_exc()}")

    def list_to_dict(self, action_dict, value, source_data):
        """
        return the index level data
        """
        try:
            if not isinstance(value, list):
                logger.warn(f"Provided value: {value} is a list type")
                return value
            key = action_dict["key"]
            _res = {}
            for item in value:
                _res[item[key]] = item
            return _res

        except Exception:
            logger.warn(f"Error while performing list to dict: error: {traceback.format_exc()}")

    def flat(self, action_dict, value, source_data):
        """
        Performs flat on nested_list which is list of lists, list of dictionaries and list of dictionary of lists.
        the flat for dictionary needs a flat_key in the action to perform the flat.
        """
        try:
            flat_type = action_dict.get("flat_type")
            return_value = None
            if flat_type.lower() == "nested_list":
                return_value = [num for sub in value for num in sub]
            elif flat_type.lower() == "list_dict":
                return_value = []
                flat_key = action_dict.get("flat_key")
                if not flat_key:
                    logger.error(f"Invalid flat_key: {flat_key}")
                    return f"Invalid flat_key: {flat_key}"
                for item in value:
                    return_value.append(item.get(flat_key))
            elif flat_type.lower() == "list_dict_list":
                flat_key = action_dict.get("flat_key")
                if not flat_key:
                    logger.error(f"Invalid flat_key: {flat_key}")
                    return f"Invalid flat_key: {flat_key}"
                return_value = []
                for item in value:
                    return_value += item.get(flat_key)

            after_process = action_dict.get("after_process")
            if after_process and isinstance(return_value, list):
                if after_process.get("action_type") == "join":
                    delimiter = after_process.get("delimiter", "")
                    return_value = delimiter.join(map(str, return_value))

            return return_value
        except Exception:
            logger.warn(f"Could not flatten value: {value}. error: {traceback.format_exc()}")

    def custom_eval(self, action_dict, value, source_data):
        """
        Performs complex evaluations.
        """
        pass

    def sum_field_in_dict_list(self, action_dict, value, source_data):
        """
        Sum the values from a list of dictionaries for a specific field.
        """
        try:
            sum_field = action_dict.get("sum_field")

            field_paths = action_dict.get("field_paths", "")
            if isinstance(field_paths, str):
                field_paths = field_paths.split(",")
            if not isinstance(field_paths, list):
                logger.warn(f"field_paths {field_paths} should either be a list or comma separated string.")
                return "Invalid Mapping."

            for field_path in field_paths:
                value_list = self.get_ele_from_path(source_data, field_path.split("."))

                if isinstance(value_list, list):
                    total_sum = 0
                    for item in value_list:
                        if isinstance(item, dict) and sum_field in item:
                            total_sum += item.get(sum_field, 0)
                    return total_sum

            return value
        except Exception:
            logger.warn(f"Error in sum_field_in_dict_list action: {traceback.format_exc()}")
            return value

    def type_cast(self, action_dict, value, source_data):
        """
        Converts the value to a specified type based on the `to_type` key in action_dict.
        """
        to_type = action_dict.get("to_type")

        try:
            # Dictionary mapping conversion types to their corresponding operations
            type_converters = {
                "int": lambda v: int(float(v)) if isinstance(v, str) else int(v),
                "float": float,
                "str": str,
                "list": lambda v: list(v.items()) if isinstance(v, dict) else list(v),
                "bool": lambda v: v.lower() in ("true", "1", "yes", "on") if isinstance(v, str) else bool(v),
            }

            # Get the appropriate conversion function or return value unmodified if type is unsupported
            converter = type_converters.get(to_type)
            if converter:
                return converter(value)
            else:
                logger.warning(f"Unsupported conversion type: {to_type}")
                return value

        except (ValueError, TypeError) as e:
            logger.warning(f"Error converting value: {value} to type {to_type}. Error: {e}")
            return value

    def execute_action(self, action_dict, value, source_data):
        """
        Responsible to execute custom actions which are added in the mapper.
        :param action_dict: action dictionary which has type of actions, dependent fields and inputs required.
        :param value: Value on which this action is needed to be performed.
        :param source_data: Data on which this action is being performed.
        :return: Returns result value after execution.
        """
        action_mapper = {
            "capitalise": self.capitalise,
            "append": self.append,
            "add": self.add,
            "divide": self.divide,
            "prepend": self.prepend,
            "multiply": self.multiply,
            "value_in": self.value_in,
            "flat": self.flat,
            "custom_eval": self.custom_eval,
            "extract_index_data": self.extract_index_data,
            "list_to_dict": self.list_to_dict,
            "sum_field_in_dict_list": self.sum_field_in_dict_list,
            "type_cast": self.type_cast,
        }
        action_type = action_dict.get("action_type")
        if action_mapper.get(action_type):
            logger.debug(f"Action: {action_type} is being executed")
            return action_mapper.get(action_type)(action_dict, value, source_data)
        else:
            logger.warn(f"Either action: {action_type} is not implemented yet or there is a typo error in mapping.")
            return "Unimplemented action"

    def get_ele_from_path(self, source_data: dict, field_path: list):
        """
        Recursively traverses through dictionary and returns the data from the path listed.
        :param source_data: Data/Dictionary from where the field should be fetched.
        :param field_path: field path
        :return: Mapped data of the path or Invalid Mapping.
        """
        if not field_path:
            return source_data
        try:
            return self.get_ele_from_path(source_data[field_path[0]], field_path[1:])
        except KeyError:
            return "Invalid mapping."
        except TypeError:
            return "Invalid Data/Mapping."
        except Exception:
            logger.warn(f"Could not fetch data. error: {traceback.format_exc()}")

    def put_ele_to_path(self, dest_dict: dict, value, dest_path: list):
        """
        Recursively find the path and Insert element to the result dictionary.
        :param dest_dict: Result dictionary where new elements are inserted.
        :param value: Element value
        :param dest_path: Path in dest dictionary to insert value
        :return: Updated dictionary
        """
        try:
            if len(dest_path) == 1:
                dest_dict[dest_path[0]] = value
                return dest_dict
            if not dest_dict.get(dest_path[0]):
                dest_dict[dest_path[0]] = {}  # is it always a dict, check ?
            return self.put_ele_to_path(dest_dict[dest_path[0]], value, dest_path[1:])
        except Exception:
            logger.warn(f"Could not insert the {value}. error: {traceback.format_exc()}")

    def transform_data(self, source_data, data_mapping, parent_data=None):
        """
        Recursively transforms the source data to destination format given in the mapping.
        :param source_data: Data which needs to be transformed.
        :param data_mapping: source to destination field mapping.
        :param parent_data: Parent of the child data. Can be used to insert parent level information to child.
        :return: Transformed data.
        """
        result = {}
        for_each = data_mapping.get("for_each")
        field_set = data_mapping.get("field_set")
        if for_each:
            for_each_res = {}
            r_list = []
            from_path = for_each["from"].split(".")
            to_path = for_each.get("to", "").split(".") or from_path
            src_list = self.get_ele_from_path(source_data, from_path)
            for each_item in src_list:
                _res = self.transform_data(each_item, for_each, parent_data)
                r_list.append(_res)
            for_each_action = for_each.get("action")
            if for_each_action:
                r_list = self.execute_action(action_dict=for_each_action, value=r_list, source_data=source_data)
            self.put_ele_to_path(for_each_res, r_list, to_path)
            return for_each_res

        elif field_set:
            for item in field_set:
                if item.get("for_each"):
                    sub_res = self.transform_data(source_data, item, source_data)
                    result.update(sub_res)
                else:
                    action = item.get("action")
                    # Implementing only fre for now, currently $ is not used yet.
                    if item.get("from"):
                        from_path = item.get("from", "").split(".")
                        if from_path[0] == "$fre_config":
                            value = getattr(self.vendor_data_object.fre_config, from_path[1])
                        elif from_path[0].startswith("$"):
                            value = getattr(self.vendor_data_object, from_path[0][1:])
                        else:
                            if item.get("from_parent"):
                                value = self.get_ele_from_path(parent_data, from_path)
                            elif from_path[0] == "$cache_objs":
                                _temp_source = self.cache_objs.get(from_path[1])
                                value = self.get_ele_from_path(_temp_source, from_path[2:])
                            else:
                                value = self.get_ele_from_path(source_data, from_path)
                    else:
                        value = item.get("default_value")
                    if action:
                        value = self.execute_action(action_dict=action, value=value, source_data=source_data)
                    if item.get("is_unique_id"):
                        self.unique_ids.add(value)
                    to_path = item.get("to", "").split(".") or item.get("from", "").split(".")
                    if item.get("add_to_cache"):
                        if not self.cache_objs.get(to_path[0]):
                            self.cache_objs[to_path[0]] = value  # any improv
                    if item.get("is_optional") and value in [
                        "Invalid mapping.",
                        "Invalid Data/Mapping.",
                    ]:
                        logger.debug(f"Either Mapping not found or Data Error for optional path: {item.get('from')}")
                        value = None
                    elif value == "Invalid mapping.":
                        logger.warn(f"Provided path is invalid. path: {item.get('from')}")
                        value = None
                    elif value == "Invalid Data/Mapping.":
                        logger.warn(f"Source data is empty. path: {item.get('from')}")
                        value = None
                    self.put_ele_to_path(result, value, to_path)

        return result
