



def magic_pipeline_iterate(group_keys = None, element_keys=None, switch_key = ""):
    if group_keys is None:
        group_keys = []
    if element_keys is None:
        element_keys = []
    def decorator(func):
        def wrapper(self, key, data_dict, **kwargs):
            if (switch_key == "") or (switch_key in kwargs.keys() and kwargs[switch_key]):
                _group_keys = group_keys[:]
                if len(_group_keys) == 0:
                    _group_keys = list(data_dict.keys())
                for group in _group_keys:
                    group_data = data_dict[group]
                    _element_keys = element_keys[:]
                    if len(_element_keys) == 0:
                        _element_keys = list(group_data.keys())
                    for ele in _element_keys:
                        ele_data = group_data[ele]
                        for index, data in enumerate(ele_data):
                            ele_data[index] = func(self, key, group, ele, index, data, **kwargs)
            return data_dict
        return wrapper
    return decorator
