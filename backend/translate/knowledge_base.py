import warnings
import re


warnings.filterwarnings("ignore", category=UserWarning)


def should_skip_entity(entity):
    date_pattern = re.compile(r"^\d{4}s?$")
    if 'category' in entity and entity['category'] == "DATE":
        return True
    if date_pattern.match(entity):
        return True
    return False


def are_relations_equal(r1, r2):
    return all(r1[attribute] == r2[attribute] for attribute in ["head", "type", "tail"])


class KB:
    def __init__(self):
        self.entities = set()
        self.relations = []

    def add_entity(self, entity):
        if entity:
            self.entities.add(entity["title"] if isinstance(entity, dict) else entity)

    def add_relation(self, relation):
        if relation not in self.relations:
            self.relations.append(relation)
