# Imperialism remake
# Copyright (C) 2015 Spitaels <spitaelsantoine@gmail.com>
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

import math
import lib.utils as u

from PySide import QtGui, QtCore
from base import constants as c
import lib.graphics as g

"""
    Defines a battle.
"""

class BattlePropertyKeyNames:
    """
        Key names for general properties of a battle map.
    """

    TITLE = ' battle.title'
    DESCRIPTION = 'battle.description'
    MAP_COLUMNS = 'map.columns'
    MAP_ROWS = 'map.rows'
    FORTIFICATION = 'fortification'
    TILE_MAXSIZE = 'title.size.max'

NEW_BATTLE_DEFAULT_PROPERTIES = {
    BattlePropertyKeyNames.TITLE: 'Battle',
    BattlePropertyKeyNames.MAP_COLUMNS: 40,
    BattlePropertyKeyNames.MAP_ROWS: 17
}

class BattleMap(QtCore.QObject):

    def __init__(self):
        """
            Start with a clean state.
        """
        super().__init__()
        self.reset()
        self.create_map(NEW_BATTLE_DEFAULT_PROPERTIES[BattlePropertyKeyNames.MAP_COLUMNS],NEW_BATTLE_DEFAULT_PROPERTIES[BattlePropertyKeyNames.MAP_ROWS])

    # noinspection PyAttributeOutsideInit
    def reset(self):
        """
            Just empty
        """
        self._properties = {BattlePropertyKeyNames.FORTIFICATION: []}
        self._provinces = {}
        self._nations = {}
        self._map = {}

    def create_map(self, columns, rows):
        """
            Given a size, constructs a map (list of two sub lists with each the number of tiles entries) which is 0.
        """
        self._properties[BattlePropertyKeyNames.MAP_COLUMNS] = columns
        self._properties[BattlePropertyKeyNames.MAP_ROWS] = rows
        number_tiles = columns * rows
        self._map['terrain'] = [0] * number_tiles
        self._map['resource'] = [0] * number_tiles

    def add_fortification(self, name, tiles):
        """
            Adds a fortification with a list of tiles and a name.
        """
        river = {
            'name': name,
            'tiles': tiles
        }
        self._properties[BattlePropertyKeyNames.FORTIFICATION].extend([river])

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
        if row < 0 or row >= self._properties[BattlePropertyKeyNames.MAP_ROWS] or column < 0\
                or column >= self._properties[BattlePropertyKeyNames.MAP_COLUMNS]:
            return -1, -1
        return column, row

    @staticmethod
    def scene_position(column, row):
        """
            Converts a map position to a scene position
        """
        # TODO move to client side, has nothing to do with server (or has it?)
        return column + (row % 2) / 2, row

    def map_index(self, column, row):
        """
            Calculates the index in the linear map for a given 2D position (first row, then column)?
        """
        index = row * self._properties[BattlePropertyKeyNames.MAP_COLUMNS] + column
        return index

    def get_neighbor_position(self, column, row, direction):
        """
            Given a positon (column, row) and a direction (c.TileDirections) return the position of the next neighbor
            tile in that direction given our staggered tile layout where the second and all other odd rows are shifted
            half a tile to the right. Returns None if we would be outside of the map area.
        """
        if direction is c.TileDirections.West:
            # west
            if column > 0:
                return [column - 1, row]
            else:
                return None
        elif direction is c.TileDirections.NorthWest:
            # north-west
            if row > 0:
                if row % 2 == 0:
                    # even rows (0, 2, 4, ..)
                    return [column - 1, row - 1]
                else:
                    # odd rows (1, 3, 5, ..)
                    return [column, row - 1]
            else:
                return None
        elif direction is c.TileDirections.NorthEast:
            # north-east
            if row > 0:
                if row % 2 == 0:
                    # even rows (0, 2, 4, ..)
                    return [column, row - 1]
                else:
                    # odd rows (1, 3, 5, ..)
                    return [column + 1, row - 1]
            else:
                return None
        elif direction is c.TileDirections.East:
            # east
            if column < self._properties[BattlePropertyKeyNames.MAP_COLUMNS] - 1:
                return [column + 1, row]
            else:
                return None
        elif direction is c.TileDirections.SouthEast:
            # south-east
            if row < self._properties[BattlePropertyKeyNames.MAP_ROWS] - 1:
                if row % 2 == 0:
                    # even rows (0, 2, 4, ..)
                    return [column, row + 1]
                else:
                    # odd rows (1, 3, 5, ..)
                    return [column + 1, row + 1]
            else:
                return None
        elif direction is c.TileDirections.SouthWest:
            # south-west
            if row < self._properties[BattlePropertyKeyNames.MAP_ROWS] - 1:
                if row % 2 == 0:
                    # even rows (0, 2, 4, ..)
                    return [column - 1, row + 1]
                else:
                    # odd rows (1, 3, 5, ..)
                    return [column, row + 1]
            else:
                return None

    def get_neighbored_tiles(self, column, row):
        """
            For all directions, get all neighbored tiles.
        """
        tiles = []
        for direction in c.TileDirections:
            tiles.append(self.get_neighbor_position(column, row, direction))
        return tiles

    def __setitem__(self, key, value):
        """
            Given a key and a value, sets a battle property.
        """
        self._properties[key] = value

    def __getitem__(self, key):
        """
            Given a key, returns a battle property. One can only obtain properties that have been set before.
        """
        if key in self._properties:
            return self._properties[key]
        else:
            raise RuntimeError('Unknown property {}.'.format(key))

    def get_terrain_name(self, terrain):
        """
            Get a special property from the rules.

            TODO move this to a special rules class. Only have rules() and setRules() here.
        """
        return self._properties['rules']['terrain.names'][terrain]

    def load_rules(self):
        """

        """
        # read rules
        rule_file = c.extend(c.Battle_Ruleset_Folder, self._properties['rules'])
        self._properties['rules'] = u.read_as_yaml(rule_file)



class BattleMapView(QtGui.QGraphicsView):
    """
        The big map holding the game map and everything.
    """

    tile_at_focus_changed = QtCore.Signal(int, int)

    def __init__(self, battle):
        super().__init__()

        self.scene = QtGui.QGraphicsScene()
        self.setScene(self.scene)
        self.setObjectName('map')
        #self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
        self.setResizeAnchor(QtGui.QGraphicsView.NoAnchor)
        self.setMouseTracking(True)
        self.current_column = -1
        self.current_row = -1
        self.battle = battle

    def redraw_map(self):
        """
            When a battle is loaded new we need to draw the whole map new.
        """
        self.scene.clear()
        self.TitleSize = self.height()/NEW_BATTLE_DEFAULT_PROPERTIES[BattlePropertyKeyNames.MAP_ROWS]
        columns = self.battle[BattlePropertyKeyNames.MAP_COLUMNS]
        rows = self.battle[BattlePropertyKeyNames.MAP_ROWS]

        width = (columns + 0.5) * self.TitleSize
        height = rows * self.TitleSize
        self.scene.setSceneRect(0, 0, width, height)


        # fill the ground layer with ocean
        item = self.scene.addRect(0, 0, width, height, brush=c.terrain_brushes[0], pen=g.TRANSPARENT_PEN)
        item.setZValue(0)

        # fill plains, hills, mountains, tundra, swamp, desert with texture

        # go through each position
        paths = {}
        for t in range(1, 7):
            paths[t] = QtGui.QPainterPath()
        for column in range(0, columns):
            for row in range(0, rows):
                t = self.battle.terrain_at(column, row)
                if t != 0:
                    # not for sea
                    sx, sy = self.battle.scene_position(column, row)
                    paths[t].addRect(sx * self.TitleSize, sy * self.TitleSize, self.TitleSize, self.TitleSize)
        for t in paths:
            path = paths[t]
            path = path.simplified()
            item = self.scene.addPath(path, brush=c.terrain_brushes[t], pen=g.TRANSPARENT_PEN)
            item.setZValue(1)

        # fill the half tiles which are not part of the map
        brush = QtGui.QBrush(QtCore.Qt.darkGreen)
        for row in range(0, rows):
            if row % 2 == 0:
                item = self.scene.addRect(columns * self.TitleSize, row * self.TitleSize, self.TitleSize / 2,
                                          self.TitleSize, pen=g.TRANSPARENT_PEN)
            else:
                item = self.scene.addRect(0, row * self.TitleSize, self.TitleSize / 2, self.TitleSize,
                                          pen=g.TRANSPARENT_PEN)
            item.setBrush(brush)
            item.setZValue(1)

        # draw the grid and the coordinates
        for column in range(0, columns):
            for row in range(0, rows):
                sx, sy = self.battle.scene_position(column, row)
                # item = self.scene.addRect(sx * self.TitleSize, sy * self.TitleSize,  self.TitleSize,  self.TitleSize)
                # item.setZValue(1000)
                text = '({},{})'.format(column, row)
                item = QtGui.QGraphicsSimpleTextItem(text)
                item.setBrush(QtGui.QBrush(QtCore.Qt.black))
                item.setPos((sx + 0.5) * self.TitleSize - item.boundingRect().width() / 2, sy * self.TitleSize)
                item.setZValue(1001)
                self.scene.addItem(item)

    def get_bounds(self):
        """
            Returns the visible part of the map view relative to the total scene rectangle as a rectangle (with all
            values between 0 and 1).
        """
        # total rectangle of the scene (0, 0, width, height)
        s = self.scene.sceneRect()
        # visible rectangle of the view
        v = self.mapToScene(self.rect()).boundingRect()
        return QtCore.QRectF(v.x() / s.width(), v.y() / s.height(), v.width() / s.width(), v.height() / s.height())

    def set_position(self, x, y):
        """
            Changes the visible part of the view.
        """
        # total rectangle of the scene (0, 0, width, height)
        s = self.scene.sceneRect()
        # visible rectangle of the view
        v = self.mapToScene(self.rect()).boundingRect()
        # adjust x, y to scene coordinates and find center
        x = x * s.width() + v.width() / 2
        y = y * s.height() + v.height() / 2
        # center on it
        self.centerOn(x, y)

    def mouseMoveEvent(self, event):
        """
            The mouse on the view has been moved. Emit signal tile_at_focus_changed if we now hover over a different tile.
        """
        # get mouse position in scene coordinates
        scene_position = self.mapToScene(event.pos()) / self.TitleSize
        column, row = self.battle.map_position(scene_position.x(), scene_position.y())
        if column != self.current_column or row != self.current_row:
            self.current_column = column
            self.current_row = row
            self.tile_at_focus_changed.emit(column, row)
        super().mouseMoveEvent(event)

    def resizeEvent(self, evt=None):
        self.redraw_map()

