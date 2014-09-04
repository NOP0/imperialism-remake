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

# TODO queue notifications

import json
from functools import partial

from PySide import QtCore, QtGui

import constants as c
import tools as t
import lib.graphics as g
import client.graphics as cg
import client.audio as audio
from lib.browser import BrowserWidget
from server.editor import EditorScreen

class MapItem(QtCore.QObject):
    def __init__(self, parent, pixmap, label, description):
        super().__init__(parent)
        # store label and description
        self.label = label
        self.description = description

        # create clickable pixmap item and create fade animation
        self.item = g.ClickablePixmapItem(pixmap)
        self.fade = g.FadeAnimation(self.item)
        self.fade.set_duration(300)

        # wire to fade in/out
        self.item.entered.connect(self.fade.fadein)
        self.item.left.connect(self.fade.fadeout)

        # wire to show/hide connection
        self.item.entered.connect(self.show_description)
        self.item.left.connect(self.hide_description)

    def show_description(self):
        self.label.setText('<font color=#ffffff size=6>{}</font>'.format(self.description))

    def hide_description(self):
        self.label.setText('')

class StartScreen(QtGui.QWidget):

    frame_pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(255, 255, 255, 64)), 6, j=QtCore.Qt.BevelJoin)

    def __init__(self, client):
        super().__init__()

        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setProperty('background', 'texture')

        layout = g.RelativeLayout(self)

        start_image = QtGui.QPixmap(c.extend(c.Graphics_UI_Folder, 'start.background.jpg'))
        start_image_item = QtGui.QGraphicsPixmapItem(start_image)
        start_image_item.setZValue(1)

        scene = QtGui.QGraphicsScene(self)
        scene.addItem(start_image_item)

        view = QtGui.QGraphicsView(scene)
        view.resize(start_image.size())
        view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        view.setSceneRect(0, 0, start_image.width(), start_image.height())
        view.layout_constraint = g.RelativeLayoutConstraint().centerH().centerV()
        layout.addWidget(view)

        subtitle = QtGui.QLabel('')
        subtitle.layout_constraint = g.RelativeLayoutConstraint((0.5, -0.5, 0),
                                                                (0.5, -0.5, start_image.height() / 2 + 20))
        layout.addWidget(subtitle)

        actions = {
            'exit': client.quit,
            'help': client.display_help_browser,
            'lobby': client.display_game_lobby_dialog,
            'editor': client.switch_to_editor_screen,
            'options': client.display_options_dialog
        }

        image_map_file = c.extend(c.Graphics_UI_Folder, 'start.overlay.info')
        with open(image_map_file, 'r') as f:
            image_map = json.load(f)

        if actions.keys() != image_map.keys():
            raise RuntimeError('Start screen hot map info file ({}) corrupt.'.format(image_map_file))

        for k, v in image_map.items():
            # add action from our predefined action dictionary
            pixmap = QtGui.QPixmap(c.extend(c.Graphics_UI_Folder, v['overlay']))
            mapitem = MapItem(view, pixmap, label=subtitle, description=v['label'])
            mapitem.item.setZValue(3)
            offset = v['offset']
            mapitem.item.setOffset(QtCore.QPointF(offset[0], offset[1]))
            mapitem.item.clicked.connect(actions[k])

            frame_path = QtGui.QPainterPath()
            frame_path.addRect(mapitem.item.boundingRect())
            frame_item = scene.addPath(frame_path, StartScreen.frame_pen)
            frame_item.setZValue(4)
            scene.addItem(mapitem.item)


        version_label = QtGui.QLabel('<font color=#ffffff>{}</font>'.format(t.options[c.O_VERSION]))
        version_label.layout_constraint = g.RelativeLayoutConstraint().east(20).south(20)
        layout.addWidget(version_label)


class GameLobbyWidget(QtGui.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtGui.QVBoxLayout(self)
        toolbar = QtGui.QToolBar()

        layout.addWidget(toolbar)
        layout.addStretch()


class OptionsContentWidget(QtGui.QTabWidget):
    def __init__(self):
        super().__init__()

        # empty lists
        self.checkboxes = []

        # add tabs
        self.add_tab_general()
        self.add_tab_music()

    def add_tab_general(self):
        tab = QtGui.QWidget()
        tab_layout = QtGui.QVBoxLayout(tab)

        # Graphics box
        box = QtGui.QGroupBox('Graphics')
        checkbox = QtGui.QCheckBox('Full screen mode')
        self.register_checkbox(checkbox, c.OG_MW_FULLSCREEN)
        layout = QtGui.QVBoxLayout(box)
        layout.addWidget(checkbox)
        tab_layout.addWidget(box)

        # vertical stretch
        tab_layout.addStretch()

        # add tab
        self.addTab(tab, 'General')

    def add_tab_music(self):
        tab = QtGui.QWidget()
        tab_layout = QtGui.QVBoxLayout(tab)

        # mute checkbox
        checkbox = QtGui.QCheckBox('Mute background music')
        self.register_checkbox(checkbox, c.OM_BG_MUTE)
        tab_layout.addWidget(checkbox)

        # vertical stretch
        tab_layout.addStretch()

        # add tab
        self.addTab(tab, 'Music')

    def register_checkbox(self, checkbox, option):
        checkbox.setChecked(t.options[option])
        self.checkboxes.append((checkbox, option))

    def close_request(self, widget):
        # check if something was changed
        options_modified = any([box.isChecked() is not t.options[option] for (box, option) in self.checkboxes])
        if options_modified:
            answer = QtGui.QMessageBox.question(widget, 'Preferences', 'Save modified preferences',
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
            if answer == QtGui.QMessageBox.Yes:
                # all checkboxes
                for (box, option) in self.checkboxes:
                    t.options[option] = box.isChecked()
                # what else do we need to do?
                if t.options[c.OM_BG_MUTE]:
                    # t.player.stop()
                    pass
                else:
                    # t.player.start()
                    pass
        return True


class MainWindow(QtGui.QWidget):
    """
        The main window (widget) which is the top level window of the application. It can be full screen or not and hold
        a single widget in a margin-less layout.
    """
    def __init__(self):
        """
            All the necessary initializations. Is shown at the end.
        """
        super().__init__()
        # set geometry
        self.setGeometry(t.options[c.OG_MW_BOUNDS])
        # set icon
        self.setWindowIcon(t.load_ui_icon('icon.ico'))
        # set title
        self.setWindowTitle('Imperialism Remake')

        # just a layout but nothing else
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.content = None

        # show in full screen, maximized or normal
        if t.options[c.OG_MW_FULLSCREEN]:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
            self.showFullScreen()
        elif t.options[c.OG_MW_MAXIMIZED]:
            self.showMaximized()
        else:
            self.show()

    def change_content_widget(self, widget):
        if self.content:
            self.layout.removeWidget(self.content)
            self.content.deleteLater()
        self.content = widget
        self.layout.addWidget(widget)


class Client():
    """
        Main class of the client, holds the help browser, the main window (full screen or not), the content of the main
        window, the audio player
    """
    def __init__(self):
        """
            Create the main window, the help browser dialog, the audio player, ...
        """
        # main window
        self.main_window = MainWindow()

        # help browser
        self.help_browser_widget = BrowserWidget(QtCore.QUrl(c.Manual_Index), t.load_ui_icon)
        self.help_dialog = cg.GameDialog(self.main_window, self.help_browser_widget, title='Help')
        self.help_dialog.setFixedSize(QtCore.QSize(800, 600))

        # for the notifications
        self.pending_notifications = []
        self.notification_position_constraint = g.RelativeLayoutConstraint().centerH().south(20)
        self.notification = None

        # audio player
        self.player = audio.Player()
        self.player.next.connect(self.audio_notification)
        self.player.set_playlist(audio.load_soundtrack_playlist())
        # start audio player if wished
        if not t.options[c.OM_BG_MUTE]:
            self.player.start()

    def audio_notification(self, title):
        """
            Special kind of notification from the audio system.
        """
        text = 'Playing {}'.format(title)
        self.schedule_notification(text)

    def schedule_notification(self, text):
        """
            Generic scheduling of a notification. Will be shown immediately if no other notification is shown, otherwise
            it will be shown as soon at the of the current list of notifications to be shown.
        """
        self.pending_notifications.append(text)
        if self.notification is None:
            self.show_next_notification()

    def show_next_notification(self):
        """
            Will be called whenever a notification is shown and was cleared. Tries to show the next one if there is one.
        """
        if len(self.pending_notifications) > 0:
            message = self.pending_notifications.pop(0)
            self.notification = g.Notification(self.main_window, message, position_constraint=self.notification_position_constraint)
            self.notification.finished.connect(self.show_next_notification)
            self.notification.show()
        else:
            self.notification = None

    def display_help_browser(self, url=None):
        """
            Displays the help browser somewhere on screen. Can set a special page if needed.
        """
        if url:
            self.help_browser_widget.displayPage(url)
        self.help_dialog.show()

    def switch_to_start_screen(self):
        """
            Switches the content of the main window to the start screen.
        """
        widget = StartScreen(self)
        self.main_window.change_content_widget(widget)

    def display_game_lobby_dialog(self):
        """
            Shows the game lobby dialog.
        """
        lobby_widget = GameLobbyWidget()
        dialog = cg.GameDialog(self.main_window, lobby_widget, delete_on_close=True, title='Game Lobby',
                               help_callback=self.display_help_browser)
        dialog.setFixedSize(QtCore.QSize(800, 600))
        dialog.show()

    def switch_to_editor_screen(self):
        """
            Switches the content of the main window to the editor screen.
        """
        widget = EditorScreen(self)
        self.main_window.change_content_widget(widget)

    def display_options_dialog(self):
        """
            Shows the preferences dialog.
        """
        options_widget = OptionsContentWidget()
        dialog = cg.GameDialog(self.main_window, options_widget, delete_on_close=True, title='Preferences',
                               help_callback=self.display_help_browser, close_callback=options_widget.close_request)
        dialog.setFixedSize(QtCore.QSize(800, 600))
        dialog.show()

    def quit(self):
        """
            Cleans up and closes the main window which causes app.exec_() to finish.
        """
        # store state in options
        t.options[c.OG_MW_BOUNDS] = self.main_window.normalGeometry()
        t.options[c.OG_MW_MAXIMIZED] = self.main_window.isMaximized()

        # audio
        # self.player.stop()

        # close the main window
        self.main_window.close()


def start():
    # create app
    app = QtGui.QApplication([])

    # TODO multiple screen support?

    # test for desktop availability
    desktop = app.desktop()
    rect = desktop.screenGeometry()
    if rect.width() < c.Screen_Min_Size[0] or rect.height() < c.Screen_Min_Size[1]:
        QtGui.QMessageBox.warning(None, 'Warning',
                                  'Actual screen size below minimal screen size {}.'.format(c.Screen_Min_Size))
        return

    # if no bounds are set, set resonable bounds
    if not c.OG_MW_BOUNDS in t.options:
        t.options[c.OG_MW_BOUNDS] = desktop.availableGeometry().adjusted(50, 50, -100, -100)
        t.options[c.OG_MW_MAXIMIZED] = True
        t.log_info('No bounds of the main window stored, start maximized')

    # load global stylesheet to app
    with open(c.Global_Stylesheet, 'r', encoding='utf-8') as file:
        style_sheet = file.read()
    app.setStyleSheet(style_sheet)

    # create client object and switch to start screen
    client = Client()
    client.switch_to_start_screen()

    t.log_info('client initialized, start Qt app execution')
    app.exec_()