# Imperialism remake
# Copyright (C) 2014 Trilarion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

"""
    Defines a scenario, can be loaded and saved. Should only be known to the server, never to the client (which is a
    thin client).
"""

import math
from PySide import QtCore

import tools as t, constants as c

# some constants
TITLE = 'title'
MAP_COLUMNS = 'map.columns'
MAP_ROWS = 'map.rows'
RIVERS = 'rivers'


def convert_keys_to_int(dict):
    return {int(k): v for k, v in dict.items()}


class Scenario(QtCore.QObject):
    """
        Has several dictionaries (properties, provinces, nations) and a list (map) defining everything.
    """

    def __init__(self):
        """
            Start with a clean state.
        """
        super().__init__()
        self.reset()

    def reset(self):
        """
            Just empty
        """
        self._properties = {}
        self._properties[RIVERS] = []
        self._provinces = {}
        self._nations = {}
        self._map = {}

    def create_map(self, columns, rows):
        """
            Given a size, constructs a map (list of two sub lists with each the number of tiles entries) which is 0.
        """
        self._properties[MAP_COLUMNS] = columns
        self._properties[MAP_ROWS] = rows
        number_tiles = columns * rows
        self._map['terrain'] = [0] * number_tiles
        self._map['resource'] = [0] * number_tiles

    def add_river(self, name, tiles):
        river = {
            'name': name,
            'tiles': tiles
        }
        self._properties[RIVERS].extend([river])

    def set_terrain_at(self, column, row, terrain):
        """
            Sets the terrain at a given position.
        """
        self._map['terrain'][self.map_index(column, row)] = terrain

    def terrain_at(self, column, row):
        """
            Returns the terrain at a given position.
        """
        return self._map['terrain'][self.map_index(column, row)]

    def set_resource_at(self, column, row, resource):
        """
            Sets the resource value at a given position.
        """
        self._map['resource'][self.map_index(column, row)] = resource

    def resource_at(self, column, row):
        """
            Returns the resource value at a given position from the map.
        """
        return self._map['resource'][self.map_index(column, row)]

    def map_position(self, x, y):
        """
            Converts a scene position to a map position (or return (-1,-1) if
        """
        column = math.floor(x - (y % 2) / 2)
        row = math.floor(y)
        if row < 0 or row >= self._properties[MAP_ROWS] or column < 0 or column >= self._properties[MAP_COLUMNS]:
            return -1, -1
        return column, row

    def scene_position(self, column, row):
        """
            Converts a map position to a scene position
        """
        return column + (row % 2) / 2, row

    def map_index(self, column, row):
        """
            Calculates the index in the linear map for a given 2D position (first row, then column)?
        """
        index = row * self._properties[MAP_COLUMNS] + column
        return index

    def get_neighbored_tiles(self, column, row):
        tiles = []
        # west
        if column > 0:
            tiles.append((column - 1, row))
        # east
        if column < self._properties[MAP_COLUMNS] - 1:
            tiles.append((column + 1, row))
        if row % 2 == 0:
            # even row (0, 2, 4, ..)
            # north
            if row > 0:
                # north-west
                if column > 0:
                    tiles.append((column - 1, row - 1))
                # north-east always exists
                tiles.append((column, row - 1))
            # south
            if row < self._properties[MAP_ROWS] - 1:
                # south-west
                if column > 0:
                    tiles.append((column - 1, row + 1))
                # south-east always exists
                tiles.append((column, row + 1))
        else:
            # odd row (1, 3, 5, ..)
            # north
            if row > 0:
                # north-west always exists
                tiles.append((column, row - 1))
                # north-east
                if column < self._properties[MAP_COLUMNS] - 1:
                    tiles.append((column + 1, row - 1))
            # south
            if row < self._properties[MAP_ROWS] - 1:
                # south-west always exists
                tiles.append((column, row + 1))
                # south-east
                if column < self._properties[MAP_COLUMNS] - 1:
                    tiles.append((column + 1, row + 1))
        return tiles

    def __setitem__(self, key, value):
        """
            Given a key and a value, sets a scenario property.
        """
        self._properties[key] = value

    def __getitem__(self, key):
        """
            Given a key, returns a scenario property. One can only obtain properties that have been set before.
        """
        if key in self._properties:
            return self._properties[key]
        else:
            raise RuntimeError('Unknown property {}.'.format(key))

    def new_province(self):
        """
            Creates a new (nation-less) province and returns it.
        """
        province = len(self._provinces)  # this always works because we check after loading
        self._provinces[province] = {}
        self._provinces[province]['tiles'] = []
        return province

    def set_province_property(self, province, key, value):
        """
            Sets a province property.
        """
        if province in self._provinces:
            self._provinces[province][key] = value
        else:
            raise RuntimeError('Unknown province {}.'.format(province))

    def get_province_property(self, province, key):
        """
            Gets a province property.
        """
        if province in self._provinces and key in self._provinces[province]:
            return self._provinces[province][key]
        else:
            raise RuntimeError('Unknown province {} or property {}.'.format(province, key))

    def add_province_map_tile(self, province, position):
        if province in self._provinces and self.is_valid_position(position):
            self._provinces[province]['tiles'].append(position)

    def all_nations(self):
        return self._nations.keys()

    def new_nation(self):
        """
            Add a new nation and returns it.
        """
        nation = len(self._nations)  # this always gives a new unique number because we check after loading
        self._nations[nation] = {}
        self._nations[nation]['properties'] = {}
        self._nations[nation]['provinces'] = []
        return nation

    def set_nation_property(self, nation, key, value):
        """
            Set nation property.
        """
        if nation in self._nations:
            self._nations[nation]['properties'][key] = value
        else:
            raise RuntimeError('Unknown nation {}.'.format(nation))

    def get_nation_property(self, nation, key):
        """
            Gets a nation property.
        """
        if nation in self._nations and key in self._nations[nation]['properties']:
            return self._nations[nation]['properties'][key]
        else:
            raise RuntimeError('Unknown nation {} or property {}.'.format(nation, key))

    def get_provinces_of_nation(self, nation):
        if nation in self._nations:
            return self._nations[nation]['provinces']
        else:
            raise RuntimeError('Unknown nation {}.'.format(nation))

    def get_province_at(self, column, row):
        position = [column, row] # internally because of JSON saving we only have []
        for province in self._provinces:
            if position in self._provinces[province]['tiles']:
                return province
        return None

    def transfer_province_to_nation(self, province, nation):
        """
            Moves a province to a nation.
        """
        # TODO this is not right yet
        self._nations[nation]['provinces'].append(province)

    def get_terrain_name(self, terrain):
        return self._properties['rules']['terrain.names'][terrain]

    def load(self, file_name):
        """
            Loads/deserializes all internal variables from a zipped archive via JSON.
        """
        self.reset()
        reader = t.ZipArchiveReader(file_name)
        self._properties = reader.read_as_json('properties')
        self._map = reader.read_as_json('map')
        self._provinces = reader.read_as_json('provinces')
        # convert keys from str to int
        self._provinces = convert_keys_to_int(self._provinces)
        # TODO check all ids are smaller then len()
        self._nations = reader.read_as_json('nations')
        # convert keys from str to int
        self._nations = convert_keys_to_int(self._nations)
        # TODO check all ids are smaller then len()
        self.load_rules()

    def load_rules(self):
        # read rules
        rule_file = c.extend(c.Scenario_Ruleset_Folder, self._properties['rules'])
        self._properties['rules'] = t.read_json(rule_file)
        # replace terrain_names
        self._properties['rules']['terrain.names'] = convert_keys_to_int(self._properties['rules']['terrain.names'])

    def save(self, file_name):
        """
            Saves/serializes all internal variables via JSON into a zipped archive.
        """
        writer = t.ZipArchiveWriter(file_name)
        writer.write_json('properties', self._properties)
        writer.write_json('map', self._map)
        writer.write_json('provinces', self._provinces)
        writer.write_json('nations', self._nations)
