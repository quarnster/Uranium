# Copyright (c) 2020 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.
from typing import Callable, Optional

from PyQt5.QtCore import Qt
from UM.FlameProfiler import pyqtSlot
from UM.Qt.ListModel import ListModel
from UM.Logger import Logger


class FileProviderModel(ListModel):
    NameRole = Qt.UserRole + 1
    DisplayTextRole = Qt.UserRole + 2
    FileProviderRole = Qt.UserRole + 3
    ShortcutRole = Qt.UserRole + 4

    def __init__(self, parent = None):
        super().__init__(parent)
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.DisplayTextRole, "displayText")
        self.addRoleName(self.FileProviderRole, "fileProvider")
        self.addRoleName(self.ShortcutRole, "shortcut")
        self._application = parent

    def initialize(self, file_provider_enabled_call_function: Optional[Callable]) -> None:
        """
        Initializes the file provider model.
        This is achieved by connecting the enabledChanged signal of all the file_providers to the given function.

        :param file_provider_enabled_call_function: The function which will be called when a file provider gets enabled
                                                    or disabled
        """
        for file_provider in self._application.getFileProviders():
            file_provider.enabledChanged.connect(file_provider_enabled_call_function)
        self.update()

    def update(self) -> None:
        """
        Updates the FileProviderModel to contain only the enabled file providers.
        """
        self.clear()

        # Always add the local file provider to the list. Since it is not really a plugin, fake an entry in the file providers
        # list and handle it in the front-end by triggering the openAction when that item is selected
        self.appendItem({
            "name"         : "LocalFileProvider",
            "displayText"  : "From Disk",
            "fileProvider" : None,  # it's not loaded via a plugin, so its FileProvider is empty
            "shortcut"     : "Ctrl+O"
        })

        for file_provider in self._application.getFileProviders():
            meta_data = self._application.getPluginRegistry().getMetaData(file_provider.getPluginId())

            if "plugin" in meta_data and file_provider.isEnabled():
                menu_item_name = file_provider.getMenuItemName()

                if not menu_item_name:
                    menu_item_name = meta_data["plugin"].get("name", None)

                self.appendItem({
                    "name": menu_item_name,
                    "displayText" : file_provider.getMenuItemDisplayText(),
                    "fileProvider": file_provider,
                    "shortcut": file_provider.getShortcut()
                })

    @pyqtSlot(str)
    def trigger(self, file_provider_name) -> None:
        """
        Safely triggers the run function of the given file_provider_name

        :param file_provider_name: The file provider which was requested to be triggered
        """
        for item in self._items:
            if item["name"] == file_provider_name:
                try:
                    item["fileProvider"].run()
                except Exception:
                    # Yes, we really want a broad exception here. These items are always plugins, and those should be
                    # kept from crashing the main application as much as possible.
                    Logger.logException("w", "Failed to activate the file provider '{}'".format(file_provider_name))
