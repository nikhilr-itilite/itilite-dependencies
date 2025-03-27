query_operators = {
    "=": "$eq",
    ">": "$gt",
    "<": "$lt",
    ">=": "$gte",
    "<=": "$lte",
    "in": "$in",
    "not_in": "$nin",
    "!=": "$ne",
    "exists": "$exists",
    "and": "$and",
    "or": "$or",
    "nor": "$nor",
    "not": "$not",
    "mod": "$mod",
    "match": "$match",
    "group": "$group",
    "push": "$push",
    "unwind": "$unwind",
    "sort": "$sort",
    "first": "$first",
}

query_operators_predicate = ["=", ">", "<", ">=", "<=", "in", "not_in", "!=", "exists"]

query_operators_conditional = ["and", "or"]
