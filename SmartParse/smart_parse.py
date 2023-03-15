'''
{
    "form_meta":
    {
        "form_name": form_type,
        "cloud" : point_cloud
        "front_center":image
        ...
    },
    "element_meta":
    {
        "front_lane": lane2d,
        "real_lane": lane3d,
        "front_box": box2d
        ...
    },
    "calibrate":{
        form1:{ },
        "form2: {},
    }

    parent_meta:
    {
        "cloud": [real_lane],
        "front_center" : [front_lane, front_box]
    }
    frame_order_list: [key1, key2, key3],
    "data":
    {
        "front_center": {
            "key1": "path/to/jpg...",
            "key2": "path/to/jpg...",
            ...
        },
        "front_left": {
            "key1": "path/to/jpg...",
            "key2": "path/to/jpg...",
            ...
        }
    },

    "element":
    {
        "front_lane":{
            "key"[
                [N*M]
                ...
            ],
            ...
        },
        "front_box":
        {
            "key":[
                [N*M],
                ...
            ],
            ....
        }
        ...
    },
    "topology":
    {
        "key" : [
            [("front_lane", index), (front_lane, index)],
            ...
        ],
        ...
    },
}


'''