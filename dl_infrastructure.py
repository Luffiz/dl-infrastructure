# -*- coding: utf-8 -*-
"""
/***************************************************************************
 dl_infrastructure
                                 A QGIS plugin
 Plugin to download latest files of
"Infrastructures électriques au dessus de 5W" from the ANFR site
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2018-09-11
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Pluffyz
        email                : none
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
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QFileDialog
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .dl_infrastructure_dialog import dl_infrastructureDialog
from bs4 import BeautifulSoup
import pandas as pd
import os.path
import webbrowser
import requests
import zipfile
import csv


class dl_infrastructure:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'dl_infrastructure_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = dl_infrastructureDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&dl_infrastructure')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'dl_infrastructure')
        self.toolbar.setObjectName(u'dl_infrastructure')

        # Declare a lineEdit object
        self.dlg.lineEdit.clear()
        self.dlg.lineEdit.setReadOnly(True)

        # Declare a new button connected to the select_dir() method
        self.dlg.pushButton.clicked.connect(self.select_dir)

        # Declare a new commandLinkButton connected to the open_anfr() method
        self.dlg.commandLinkButton.pressed.connect(self.open_anfr)

        # Declare a new button connected to the main installation method.
        self.dlg.pushButton_2.pressed.connect(self.installation)
        self.dlg.pushButton_2.setDisabled(True)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('dl_infrastructure', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/dl_infrastructure/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Get the latest version of the ANFR Data'),
            callback=self.run,
            parent=self.iface.mainWindow())
        self.dlg.progressBar.setValue(0)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&dl_infrastructure'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            return

    # Main method of the program : used to call on others
    def installation(self):
        antenna_dir = os.path.join(path_dir, 'Latest_antenna.zip')
        ref_dir = os.path.join(path_dir, 'Latest_ref.zip')

        self.get_data()

        self.unzip_file(antenna_dir)
        self.unzip_file(ref_dir)
        self.txt_to_csv()

        self.creation_Supports()
        self.creation_Antennes()
        self.creation_Bandes()

        self.clean_dir()

    # Open a new tab of the ANFR website
    def open_anfr(self):
        webbrowser.open('https://tinyurl.com/ybcoxj8y')

    # Set the download directory depending on user's choice.
    def select_dir(self):
        global path_dir
        path_dir = QFileDialog.getExistingDirectory(
            self.dlg, "Choose your directory", "", QFileDialog.ShowDirsOnly)
        self.dlg.lineEdit.setText(path_dir)
        if self.dlg.lineEdit.text() is not '':
            self.dlg.pushButton_2.setDisabled(False)

    # Used to convert the different .txt files to .csv
    def txt_to_csv(self):
        fichiers = os.listdir(path_dir)
        for fichier in fichiers:
            if '.txt' in fichier:
                fichier = os.path.join(path_dir, fichier)
                read_csv = csv.reader(open(os.path.join(path_dir, fichier), "r", encoding='latin1'), delimiter=';') # noqa E501

                newfichier = fichier.replace('.txt', '.csv')
                name_newfichier = os.path.join(path_dir, newfichier)

                fichier_csv = csv.writer(open(name_newfichier, 'w', encoding='latin1')) # noqa E501
                fichier_csv.writerows(read_csv)
                os.remove(fichier)
        self.dlg.progressBar.setValue(10)

    # Will unzip the different files downloaded
    def unzip_file(self, ch_fichier):
        with zipfile.ZipFile(ch_fichier, "r") as dezip:
            dezip.extractall(path_dir)
            dezip.close()
            os.remove(ch_fichier)

    # Method which will generate a Support Table used by the other creation_methods
    def model_support(self):
        sup_dir = os.path.join(path_dir, 'SUP_SUPPORT.csv')
        sup_full_dir = os.path.join(path_dir, 'SUP_FULL_SUPPORT.csv')

        with open(sup_dir, "r", encoding="latin1") as source, open(sup_full_dir, "w") as result: # noqa E501
                rdr = csv.reader(source, delimiter=',')
                wtr = csv.writer(result)
                for r in rdr:
                    wtr.writerow([r[0]] + [r[1]] + [r[2]] +
                                 [r[3] + "°" + r[4] + "'" + r[5] + "''" + r[6]] + # noqa E501
                                 [r[7] + "°" + r[8] + "'" + r[9] + "''" + r[10]] + # noqa E501 
                                 [r[11]] + [r[12]] + [r[13]] + [r[14]] +
                                 [r[15]] + [r[16]] + [r[17]] + [r[18]])
        sup = pd.read_csv(
            sup_full_dir, names=['SUP_ID', 'STA_NM_ANFR', 'NAT_ID',
                                 'LATITUDE', 'LONGITUDE', 'SUP_NM_HAUT',
                                 'TPO_ID', 'ADR_LB_LIEU', 'ADR_LB_ADD1',
                                 'ADR_LB_ADD2', 'ADR_LB_ADD3', 'ADR_NM_CP',
                                 'COM_CD_INSEE'], header=0, sep=",")
        return sup

    # Method generating the Supports layer, writing as Supports.csv
    def creation_Supports(self):
        propri_dir = os.path.join(path_dir, 'SUP_PROPRIETAIRE.csv')
        explo_dir = os.path.join(path_dir, 'SUP_EXPLOITANT.csv')
        nat_dir = os.path.join(path_dir, 'SUP_NATURE.csv')
        sta_dir = os.path.join(path_dir, 'SUP_STATION.csv')

        sup_full_dir = os.path.join(path_dir, 'Supports.csv')

        sup = self.model_support()
        sta = pd.read_csv(sta_dir, sep=",", dtype=str)
        nat = pd.read_csv(nat_dir, sep=",")
        propri = pd.read_csv(propri_dir, sep=",")
        explo = pd.read_csv(explo_dir, sep=",", dtype=str)

        combi = pd.merge(sup, sta, on="STA_NM_ANFR", how='left', validate="m:1") # noqa E501
        combi_nat = pd.merge(combi, nat, on="NAT_ID", how="left")
        combi_propri = pd.merge(combi_nat, propri, on="TPO_ID", how="left")
        combi_full = pd.merge(combi_propri, explo, on="ADM_ID", how="left")
        combi_full.to_csv(sup_full_dir, index=False)

        uri_sup = ('file://%s?crs=%s&delimiter=%s&xyDms=%s&xField=%s&yField=%s' % # noqa E501
                   (sup_full_dir, 'WGS84', ',', True, 'LONGITUDE', 'LATITUDE')) # noqa E501

        self.iface.addVectorLayer(uri_sup, "Supports", "delimitedtext")
        self.dlg.progressBar.setValue(25)

    # Method generating the Antennes layer, writing as Antennes.csv
    def creation_Antennes(self):
        sta_dir = os.path.join(path_dir, 'SUP_STATION.csv')
        type_ant_dir = os.path.join(path_dir, 'SUP_TYPE_ANTENNE.csv')
        ant_dir = os.path.join(path_dir, 'SUP_ANTENNE.csv')

        ant_full_dir = os.path.join(path_dir, 'Antennes.csv')

        sup = self.model_support()
        sta = pd.read_csv(sta_dir, sep=",")
        ant = pd.read_csv(ant_dir, sep=",")
        type_ant = pd.read_csv(type_ant_dir, sep=",")

        comb_nodup = pd.merge(sup, sta, on="STA_NM_ANFR", how='left', validate="m:1").drop_duplicates(subset=['STA_NM_ANFR']) # noqa E501

        base_ant = pd.merge(ant, comb_nodup[["STA_NM_ANFR", "LONGITUDE", "LATITUDE"]], on="STA_NM_ANFR", how='left') # noqa E501
        ant_full = pd.merge(base_ant, type_ant, on="TAE_ID", how="left") # noqa E501
        ant_full.to_csv(ant_full_dir, index=False)

        uri_ant = ('file://%s?crs=%s&delimiter=%s&xyDms=%s&xField=%s&yField=%s' % # noqa E501
                    (ant_full_dir, 'WGS84', ',',True, 'LONGITUDE', 'LATITUDE')) # noqa E501

        self.iface.addVectorLayer(uri_ant, "Antennes", "delimitedtext")
        self.dlg.progressBar.setValue(50)

    # Method generating the Bandes layer, writing as Bandes.csv
    def creation_Bandes(self):

        sta_dir = os.path.join(path_dir, 'SUP_STATION.csv')
        emt_dir = os.path.join(path_dir, 'SUP_EMETTEUR.csv')
        bnd_dir = os.path.join(path_dir, 'SUP_BANDE.csv')
        bnd_full_dir = os.path.join(path_dir, 'Bandes.csv')

        bnd = pd.read_csv(bnd_dir, sep=",", dtype=str)
        emt = pd.read_csv(emt_dir, sep=",", dtype=str)
        sta = pd.read_csv(sta_dir, sep=",")
        sup = self.model_support()

        comb_nodup = pd.merge(sup, sta, on="STA_NM_ANFR", how='left', validate="m:1").drop_duplicates(subset=['STA_NM_ANFR']) # noqa E501
        bnd_base = pd.merge(bnd, comb_nodup[['STA_NM_ANFR', 'LONGITUDE', 'LATITUDE', 'SUP_ID']], on='STA_NM_ANFR', how='left') # noqa E501
        bnd_full = pd.merge(bnd_base, emt[['EMR_ID', 'EMR_LB_SYSTEME', 'AER_ID']], on='EMR_ID', how='left') # noqa E501
        bnd_full.to_csv(bnd_full_dir, index=False)

        uri_bnd = ('file://%s?crs=%s&delimiter=%s&xyDms=%s&xField=%s&yField=%s' % # noqa E501
                    (bnd_full_dir, 'WGS84', ',',True, 'LONGITUDE', 'LATITUDE')) # noqa E501

        self.iface.addVectorLayer(uri_bnd, "Bandes", "delimitedtext")
        self.dlg.progressBar.setValue(90)

    # Clean-up the directory choosed by the user, leaving only the 3 layers
    def clean_dir(self):

        fichiers = os.listdir(path_dir)
        for fichier in fichiers:
            if 'SUP_' in fichier:
                fichier = os.path.join(path_dir, fichier)
                os.remove(fichier)
        self.dlg.progressBar.setValue(100)

    # Get the latest available data on the ANFR website
    def get_data(self):

        antenna_dir = os.path.join(path_dir, 'Latest_antenna.zip')
        ref_dir = os.path.join(path_dir, 'Latest_ref.zip')
        site_url = 'https://www.data.gouv.fr/fr/datasets/donnees-sur-les-installations-radioelectriques-de-plus-de-5-watts-1/' # noqa E501
        html = requests.get(site_url)
        soup = BeautifulSoup(html.text, 'lxml')
        urls = []

        for h in soup.find_all('article', limit=2):
            a = h.find('a')
            urls.append(a.attrs['href'])

        r_ant = requests.get(urls[0])
        r_ref = requests.get(urls[1])

        with open(antenna_dir, 'wb') as f:
            f.write(r_ant.content)
        with open(ref_dir, 'wb') as f:
            f.write(r_ref.content)