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

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt import QtGui
from qgis.utils import iface
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *

import importlib, inspect
from .other_data_sources.source import Source

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Geo_Data_dialog_base.ui'))


class GeoDataDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(GeoDataDialog, self).__init__(parent)
        self.iface = iface
        self.setupUi(self)
        self.pushbutton_print.clicked.connect(self.load_data_sources)
        self.pushbutton_test.clicked.connect(self.load_wms)
        self.pushButtonLoadOtherDataSources.clicked.connect(self.load_other_data_sources)
        self.pushButtonLoadRuianPlugin.clicked.connect(self.load_ruian_plugin)
        self.data_sources = []
        self.other_data_sources = []

    def get_url(self, config):
        if config['general']['type'] == 'WMS':
            # TODO check CRS? Maybe.
            return 'url=' + config['wms']['url'] + "&layers=" + config['wms']['layers'] + "&styles=" + config['wms']['styles'] + "&" + config['wms']['params']

        if config['general']['type'] == 'TMS':
            return "type=xyz&url=" + config['tms']['url']

    def load_data_sources(self):
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        sources_dir = os.path.join(current_dir, 'data_sources')

        paths = []

        for name in os.listdir(sources_dir):
            if os.path.isdir(os.path.join(sources_dir, name)):
                paths.append(name)

        config = configparser.ConfigParser()

        index = 0
        for path in paths:
            config.read(os.path.join(sources_dir, path, 'metadata.ini'))
            # print(config.sections())
            # for key in config['gdal']:
            #     print(key)
            # print(config['gdal']['source_file'])
            self.add_item_to_list(config['ui']['alias'], index)
            # TODO check type of sources then add adequate prefix or parameters
            url = self.get_url(config)
            print(url)
            self.data_sources.append(
                {
                    "alias": config['ui']['alias'],
                    "url": url
                }
            )
            index += 1
            # self.wms_sources.append(config['gdal']['url=http://kaart.maaamet.ee/wms/alus&format=image/png&layers=MA-ALUS&styles=&crs=EPSG:3301'])

    def add_item_to_list(self, label, index):
        itemN = QtWidgets.QListWidgetItem()
        widget = QtWidgets.QWidget()
        widgetText = QtWidgets.QLabel(label)
        widgetButton = QtWidgets.QPushButton("Add Layer")
        widgetButton.clicked.connect(lambda: self.add_layer(index))
        widgetLayout = QtWidgets.QHBoxLayout()
        widgetLayout.addWidget(widgetText)
        widgetLayout.addWidget(widgetButton)
        widgetLayout.addStretch()
        widgetLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        widget.setLayout(widgetLayout)
        itemN.setSizeHint(widget.sizeHint())
        widget.show()
        # Add widget to QListWidget funList
        self.listWidget.addItem(itemN)
        self.listWidget.setItemWidget(itemN, widget)

    def add_layer(self, index):
        # print("Add Layer " + (self.wms_sources[index]))
        # rlayer = QgsRasterLayer(self.wms_sources[index], 'MA-ALUS', 'wms')
        layer = QgsRasterLayer(self.data_sources[index]['url'], self.data_sources[index]['alias'], 'wms')
        # TODO check if the layer is valid
        QgsProject.instance().addMapLayer(layer)

    def load_wms(self):
        # urlWithParams = 'url=http://kaart.maaamet.ee/wms/alus&format=image/png&layers=MA-ALUS&styles=&crs=EPSG:3301'
        urlWithParams = 'url=http://geoportal.cuzk.cz/WMS_ORTOFOTO_PUB/WMService.aspx&styles=&layers=GR_ORTFOTORGB&format=image/png&crs=EPSG:5514'
        rlayer = QgsRasterLayer(urlWithParams, 'CUZK', 'wms')
        QgsProject.instance().addMapLayer(rlayer)

    # add MapTiler Collection to Browser
    def initGui(self):
        self.dip = DataItemProvider()
        QgsApplication.instance().dataItemProviderRegistry().addProvider(self.dip)

        self._activate_copyrights

    def addToBrowser(self):
        # Sources
        sources = []
        sources.append(["connections-xyz", "Google Maps", "", "", "", "https://mt1.google.com/vt/lyrs=m&x=%7Bx%7D&y=%7By%7D&z=%7Bz%7D", "", "19", "0"])
        sources.append(["connections-xyz", "Stamen Terrain", "", "", "Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL",
                        "http://tile.stamen.com/terrain/%7Bz%7D/%7Bx%7D/%7By%7D.png", "", "20", "0"])

        # Add sources to browser
        for source in sources:
            connectionType = source[0]
            connectionName = source[1]
            QSettings().setValue("qgis/%s/%s/authcfg" % (connectionType, connectionName), source[2])
            QSettings().setValue("qgis/%s/%s/password" % (connectionType, connectionName), source[3])
            QSettings().setValue("qgis/%s/%s/referer" % (connectionType, connectionName), source[4])
            QSettings().setValue("qgis/%s/%s/url" % (connectionType, connectionName), source[5])
            QSettings().setValue("qgis/%s/%s/username" % (connectionType, connectionName), source[6])
            QSettings().setValue("qgis/%s/%s/zmax" % (connectionType, connectionName), source[7])
            QSettings().setValue("qgis/%s/%s/zmin" % (connectionType, connectionName), source[8])

        # Update GUI
        iface.reloadConnections()

    def load_other_data_sources(self):
        # Used from https://stackoverflow.com/questions/3178285/list-classes-in-directory-python
        self.other_data_sources = []
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        current_module_name = os.path.splitext(os.path.basename(current_dir))[0]
        sources_dir = os.path.join(current_dir, 'other_data_sources')
        paths = [ name for name in os.listdir(sources_dir) if os.path.isdir(os.path.join(sources_dir, name)) ]
        index = 0
        for path in paths:
            if not path.startswith("__"):
                module = importlib.import_module(".other_data_sources." + path + ".source", package=current_module_name)
                for member in dir(module):
                    if member != 'Source':
                        handler_class = getattr(module, member)
                        if handler_class and inspect.isclass(handler_class) and issubclass(handler_class, Source):
                            current_source = handler_class()
                            self.other_data_sources.append(current_source)
                            # TODO list all layers not just a sources
                            self.add_other_data_source_item_to_list(current_source.get_metadata().name, index)
                            index += 1

    def add_other_data_source_item_to_list(self, label, index):
        itemN = QtWidgets.QListWidgetItem()
        widget = QtWidgets.QWidget()
        widgetText = QtWidgets.QLabel(label)
        widgetButton = QtWidgets.QPushButton("Add Layer")
        widgetButton.clicked.connect(lambda: self.add_other_data_source_layer(index))
        widgetLayout = QtWidgets.QHBoxLayout()
        widgetLayout.addWidget(widgetText)
        widgetLayout.addWidget(widgetButton)
        widgetLayout.addStretch()
        widgetLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        widget.setLayout(widgetLayout)
        itemN.setSizeHint(widget.sizeHint())
        widget.show()
        # Add widget to QListWidget funList
        self.listWidgetOtherDataSources.addItem(itemN)
        self.listWidgetOtherDataSources.setItemWidget(itemN, widget)

    def add_other_data_source_layer(self, index):
        vector = self.other_data_sources[index].get_vector(0, self.get_extent(), self.get_epsg())
        if vector is not None:
            QgsProject.instance().addMapLayer(vector)

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
