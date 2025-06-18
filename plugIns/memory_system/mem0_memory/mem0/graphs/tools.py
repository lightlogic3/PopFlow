UPDATE_MEMORY_TOOL_GRAPH = {
    "type": "function",
    "function": {
        "name": "update_graph_memory",
        "description": "基于新信息更新现有图记忆中的关系键。当需要修改知识图中的现有关系时，应调用此函数。只有在新信息比现有信息更近期、更准确或提供额外上下文的情况下才应执行更新。关系的源节点和目标节点必须与现有图记忆中的保持一致；只能更新关系本身。",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "要更新的关系中源节点的标识符。这应该与图中的现有节点匹配。",
                },
                "destination": {
                    "type": "string",
                    "description": "要更新的关系中目标节点的标识符。这应该与图中的现有节点匹配。",
                },
                "relationship": {
                    "type": "string",
                    "description": "源节点和目标节点之间的新关系或更新后的关系。这应该是对两个节点如何连接的简洁、清晰的描述。",
                },
            },
            "required": ["source", "destination", "relationship"],
            "additionalProperties": False,
        },
    },
}

ADD_MEMORY_TOOL_GRAPH = {
    "type": "function",
    "function": {
        "name": "add_graph_memory",
        "description": "向知识图添加新的图记忆。此函数在两个节点之间创建新的关系，如果节点不存在，则可能创建新节点。",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "新关系中源节点的标识符。这可以是现有节点或要创建的新节点。",
                },
                "destination": {
                    "type": "string",
                    "description": "新关系中目标节点的标识符。这可以是现有节点或要创建的新节点。",
                },
                "relationship": {
                    "type": "string",
                    "description": "源节点和目标节点之间的关系类型。这应该是对两个节点如何连接的简洁、清晰的描述。",
                },
                "source_type": {
                    "type": "string",
                    "description": "源节点的类型或类别。这有助于对图中的节点进行分类和组织。",
                },
                "destination_type": {
                    "type": "string",
                    "description": "目标节点的类型或类别。这有助于对图中的节点进行分类和组织。",
                },
            },
            "required": [
                "source",
                "destination",
                "relationship",
                "source_type",
                "destination_type",
            ],
            "additionalProperties": False,
        },
    },
}


NOOP_TOOL = {
    "type": "function",
    "function": {
        "name": "noop",
        "description": "不应对图实体执行任何操作。当系统根据当前输入或上下文确定不需要进行任何更改或添加时调用此函数。它作为一个占位符动作，当不需要其他动作时使用，确保系统可以明确确认无需修改图的情况。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
}


RELATIONS_TOOL = {
    "type": "function",
    "function": {
        "name": "establish_relationships",
        "description": "根据提供的文本建立实体之间的关系。",
        "parameters": {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string", "description": "关系的源实体。"},
                            "relationship": {
                                "type": "string",
                                "description": "源实体和目标实体之间的关系。",
                            },
                            "destination": {
                                "type": "string",
                                "description": "关系的目标实体。",
                            },
                        },
                        "required": [
                            "source",
                            "relationship",
                            "destination",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["entities"],
            "additionalProperties": False,
        },
    },
}


EXTRACT_ENTITIES_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_entities",
        "description": "从文本中提取实体及其类型。",
        "parameters": {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "entity": {"type": "string", "description": "实体的名称或标识符。"},
                            "entity_type": {"type": "string", "description": "实体的类型或类别。"},
                        },
                        "required": ["entity", "entity_type"],
                        "additionalProperties": False,
                    },
                    "description": "包含实体及其类型的数组。",
                }
            },
            "required": ["entities"],
            "additionalProperties": False,
        },
    },
}

UPDATE_MEMORY_STRUCT_TOOL_GRAPH = {
    "type": "function",
    "function": {
        "name": "update_graph_memory",
        "description": "基于新信息更新现有图记忆中的关系键。当需要修改知识图中的现有关系时，应调用此函数。只有在新信息比现有信息更近期、更准确或提供额外上下文的情况下才应执行更新。关系的源节点和目标节点必须与现有图记忆中的保持一致；只能更新关系本身。",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "要更新的关系中源节点的标识符。这应该与图中的现有节点匹配。",
                },
                "destination": {
                    "type": "string",
                    "description": "要更新的关系中目标节点的标识符。这应该与图中的现有节点匹配。",
                },
                "relationship": {
                    "type": "string",
                    "description": "源节点和目标节点之间的新关系或更新后的关系。这应该是对两个节点如何连接的简洁、清晰的描述。",
                },
            },
            "required": ["source", "destination", "relationship"],
            "additionalProperties": False,
        },
    },
}

ADD_MEMORY_STRUCT_TOOL_GRAPH = {
    "type": "function",
    "function": {
        "name": "add_graph_memory",
        "description": "向知识图添加新的图记忆。此函数在两个节点之间创建新的关系，如果节点不存在，则可能创建新节点。",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "新关系中源节点的标识符。这可以是现有节点或要创建的新节点。",
                },
                "destination": {
                    "type": "string",
                    "description": "新关系中目标节点的标识符。这可以是现有节点或要创建的新节点。",
                },
                "relationship": {
                    "type": "string",
                    "description": "源节点和目标节点之间的关系类型。这应该是对两个节点如何连接的简洁、清晰的描述。",
                },
                "source_type": {
                    "type": "string",
                    "description": "源节点的类型或类别。这有助于对图中的节点进行分类和组织。",
                },
                "destination_type": {
                    "type": "string",
                    "description": "目标节点的类型或类别。这有助于对图中的节点进行分类和组织。",
                },
            },
            "required": [
                "source",
                "destination",
                "relationship",
                "source_type",
                "destination_type",
            ],
            "additionalProperties": False,
        },
    },
}


NOOP_STRUCT_TOOL = {
    "type": "function",
    "function": {
        "name": "noop",
        "description": "不应对图实体执行任何操作。当系统根据当前输入或上下文确定不需要进行任何更改或添加时调用此函数。它作为一个占位符动作，当不需要其他动作时使用，确保系统可以明确确认无需修改图的情况。",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
}

RELATIONS_STRUCT_TOOL = {
    "type": "function",
    "function": {
        "name": "establish_relations",
        "description": "根据提供的文本建立实体之间的关系。",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_entity": {
                                "type": "string",
                                "description": "关系的源实体。",
                            },
                            "relatationship": {
                                "type": "string",
                                "description": "源实体和目标实体之间的关系。",
                            },
                            "destination_entity": {
                                "type": "string",
                                "description": "关系的目标实体。",
                            },
                        },
                        "required": [
                            "source_entity",
                            "relatationship",
                            "destination_entity",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["entities"],
            "additionalProperties": False,
        },
    },
}


EXTRACT_ENTITIES_STRUCT_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_entities",
        "description": "从文本中提取实体及其类型。",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "entity": {"type": "string", "description": "实体的名称或标识符。"},
                            "entity_type": {"type": "string", "description": "实体的类型或类别。"},
                        },
                        "required": ["entity", "entity_type"],
                        "additionalProperties": False,
                    },
                    "description": "包含实体及其类型的数组。",
                }
            },
            "required": ["entities"],
            "additionalProperties": False,
        },
    },
}

DELETE_MEMORY_STRUCT_TOOL_GRAPH = {
    "type": "function",
    "function": {
        "name": "delete_graph_memory",
        "description": "删除两个节点之间的关系。此函数删除现有关系。",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "关系中源节点的标识符。",
                },
                "relationship": {
                    "type": "string",
                    "description": "源节点和目标节点之间需要删除的现有关系。",
                },
                "destination": {
                    "type": "string",
                    "description": "关系中目标节点的标识符。",
                },
            },
            "required": [
                "source",
                "relationship",
                "destination",
            ],
            "additionalProperties": False,
        },
    },
}

DELETE_MEMORY_TOOL_GRAPH = {
    "type": "function",
    "function": {
        "name": "delete_graph_memory",
        "description": "删除两个节点之间的关系。此函数删除现有关系。",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "关系中源节点的标识符。",
                },
                "relationship": {
                    "type": "string",
                    "description": "源节点和目标节点之间需要删除的现有关系。",
                },
                "destination": {
                    "type": "string",
                    "description": "关系中目标节点的标识符。",
                },
            },
            "required": [
                "source",
                "relationship",
                "destination",
            ],
            "additionalProperties": False,
        },
    },
}
