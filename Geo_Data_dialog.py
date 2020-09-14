# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoDataDialog
                                 A QGIS plugin
 This plugin gathers cz/sk data sources.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-08-04
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Test
        email                : test
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import configparser
import sys
import webbrowser

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt import QtGui
from qgis.utils import iface
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *

import importlib, inspect
from .data_sources.source import Source

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Geo_Data_dialog_base.ui'))


class GeoDataDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(GeoDataDialog, self).__init__(parent)
        self.iface = iface
        self.setupUi(self)
        self.pushButtonAbout.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons/cropped-opengeolabs-logo-small.png")))
        self.pushButtonAbout.clicked.connect(self.showAbout)
        self.pushButtonLoadRuianPlugin.clicked.connect(self.load_ruian_plugin)
        self.pushButtonLoadData.clicked.connect(self.load_data)
        self.data_sources = []
        self.other_data_sources = []
        self.load_sources_into_tree()

    def get_url(self, config):
        if config['general']['type'] == 'WMS':
            # TODO check CRS? Maybe.
            return 'url=' + config['wms']['url'] + "&layers=" + config['wms']['layers'] + "&styles=" + config['wms']['styles'] + "&" + config['wms']['params']

        if config['general']['type'] == 'TMS':
            return "type=xyz&url=" + config['tms']['url']

    def load_data(self):
        # print("LOAD DATA")
        for data_source in self.data_sources:
            # print(data_source)
            if data_source['checked'] == "True":
                if "WMS" in data_source['type'] or "TMS" in data_source['type']:
                    self.add_layer(data_source)
                    self.addSourceToBrowser(data_source)
                if "PROC" in data_source['type']:
                    if data_source['proc_class'] is not None:
                        self.add_proc_data_source_layer(data_source)

    def load_sources_into_tree(self):

        self.treeWidgetSources.itemChanged.connect(self.handleChanged)
        tree    = self.treeWidgetSources
        paths = []

        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        sources_dir = os.path.join(current_dir, 'data_sources')

        for name in os.listdir(sources_dir):
            if os.path.isdir(os.path.join(sources_dir, name)) and name[:2] != "__":
                paths.append(name)

        paths.sort()
        config = configparser.ConfigParser()
        group = ""

        index = 0

        for path in paths:
            config.read(os.path.join(sources_dir, path, 'metadata.ini'))
            current_group = path.split("_")[0]
            if current_group != group:
                group = current_group
                parent = QTreeWidgetItem(tree)
                parent.setText(0, current_group) # TODO read from metadata.ini (maybe)
                parent.setFlags(parent.flags()
                  | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

            url = ""
            if "WMS" in config['general']['type'] or "TMS" in config['general']['type']:
                url = self.get_url(config)

            proc_class = None
            if "PROC" in config['general']['type']:
                proc_class = self.get_proc_class(path)

            self.data_sources.append(
                {
                    "type": config['general']['type'],
                    "alias": config['ui']['alias'],
                    "url": url,
                    "checked": config['ui']['checked'],
                    "proc_class": proc_class
                }
            )
            child = QTreeWidgetItem(parent)
            child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
            child.setText(0, config['ui']['alias'])
            child.setIcon(0, QIcon(os.path.join(sources_dir, path, config['ui']['icon'])))
            parent.setIcon(0, QIcon(os.path.join(sources_dir, path, config['ui']['icon'])))
            child.setData(0, Qt.UserRole, index)
            if config['ui']['checked'] == "True":
                child.setCheckState(0, Qt.Checked)
            else:
                child.setCheckState(0, Qt.Unchecked)
            index += 1

    def handleChanged(self, item, column):
        # Get his status when the check status changes.
        if item.data(0, Qt.UserRole) is not None:
            id = int(item.data(0, Qt.UserRole))
            if item.checkState(column) == Qt.Checked:
                # print("checked", item, item.text(column))
                self.data_sources[id]['checked'] = "True"
            if item.checkState(column) == Qt.Unchecked:
                # print("unchecked", item, item.text(column))
                self.data_sources[id]['checked'] = "False"
            # print(item.data(0, Qt.UserRole))

    def add_layer(self, data_source):
        # print("Add Layer " + (self.wms_sources[index]))
        # rlayer = QgsRasterLayer(self.wms_sources[index], 'MA-ALUS', 'wms')
        layer = QgsRasterLayer(data_source['url'], data_source['alias'], 'wms')
        # TODO check if the layer is valid
        QgsProject.instance().addMapLayer(layer)

    def get_proc_class(self, path):
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        current_module_name = os.path.splitext(os.path.basename(current_dir))[0]
        module = importlib.import_module(".data_sources." + path + ".source", package=current_module_name)
        for member in dir(module):
            if member != 'Source':
                handler_class = getattr(module, member)
                # if member == 'SampleOne':
                #     print("GPC")
                #     print(handler_class)
                #     print(inspect.isclass(handler_class))
                #     print(issubclass(handler_class, Source))
                if handler_class and inspect.isclass(handler_class) and issubclass(handler_class, Source):
                    current_source = handler_class()
                    return current_source
        return None

    def addSourceToBrowser(self, data_source):
        source = None
        if data_source['type'] == "TMS":
            url = data_source['url'][13:]
            source = ["connections-xyz", data_source['alias'], "", "", "", url, "", "19", "0"]
        if data_source['type'] == "WMS":
            url = data_source['url'][4:].split("&")[0]
            source = ["connections-wms", data_source['alias'], "", "", "", url, "", "19", "0"]
        if source != None:
            connectionType = source[0]
            connectionName = source[1]
            QSettings().setValue("qgis/%s/%s/authcfg" % (connectionType, connectionName), source[2])
            QSettings().setValue("qgis/%s/%s/password" % (connectionType, connectionName), source[3])
            QSettings().setValue("qgis/%s/%s/referer" % (connectionType, connectionName), source[4])
            QSettings().setValue("qgis/%s/%s/url" % (connectionType, connectionName), source[5])
            QSettings().setValue("qgis/%s/%s/username" % (connectionType, connectionName), source[6])
            QSettings().setValue("qgis/%s/%s/zmax" % (connectionType, connectionName), source[7])
            QSettings().setValue("qgis/%s/%s/zmin" % (connectionType, connectionName), source[8])

        iface.reloadConnections()

    def add_proc_data_source_layer(self, data_source):
        if data_source['type'] == "PROC_VEC":
            layer = data_source['proc_class'].get_vector(self.get_extent(), self.get_epsg())
        if data_source['type'] == "PROC_RAS":
            layer = data_source['proc_class'].get_raster(self.get_extent(), self.get_epsg())
        if layer is not None:
            QgsProject.instance().addMapLayer(layer)

    def get_extent(self):
        return self.iface.mapCanvas().extent()

    def get_epsg(self):
        srs = self.iface.mapCanvas().mapSettings().destinationCrs()
        return srs.authid()

    def load_ruian_plugin(self):
        ruian_found = False
        for x in iface.mainWindow().findChildren(QAction):
            if "RUIAN" in x.toolTip():
                ruian_found = True
                x.trigger()

        if not ruian_found:
            self.labelRuianError.setText("This functionality requires RUIAN plugin")

    def showAbout(self):
        try:
            webbrowser.get().open("http://opengeolabs.cz")
        except (webbrowser.Error):
            self.iface.messageBar().pushMessage(QApplication.translate("GeoData", "Error", None), QApplication.translate("GeoData", "Can not find web browser to open page about", None), level=Qgis.Critical)
