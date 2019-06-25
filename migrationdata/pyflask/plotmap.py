import pandas as pd
from base64 import b64encode
import folium
import branca
import json
from branca.element import MacroElement
from branca.colormap import LinearColormap
from jinja2 import Template
from folium import plugins

class BindColormap(MacroElement):
    def __init__(self, layer, colormap):
        super(BindColormap, self).__init__()
        self.layer = layer
        self.colormap = colormap
        self._template = Template(u"""
        {% macro script(this, kwargs) %}
            {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
            {{this._parent.get_name()}}.on('overlayadd', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
                }});
            {{this._parent.get_name()}}.on('overlayremove', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'none';
                }});
        {% endmacro %}
        """)


class baseMap():
    def __init__(self, data='None', shapefile=None):
        self.map = folium.Map(location=[2, -2], zoom_start=3)
        self.feature_groups = {}
        if type(data) == str:
            if data == 'None':
                self.df = pd.DataFrame(columns=['baseMap'])
            elif data[-4:] == '.csv':
                self.df = pd.read_csv(data)
            else:
                print('Enter path to a csv file')
        else:
            self.df = data
        if shapefile == None:
            pass
        elif shapefile[-8:] == '.geojson':
            self.geodata = json.load(open(shapefile))
        else:
            print("Enter a GeoJson file.")

    def groupedLayerControl(self, radio=[]):
        for i in self.feature_groups.keys():
            if i in radio:
                self.feature_groups[i]['None'] = folium.map.FeatureGroup(name='None', show=False).add_to(self.map)
        folium.plugins.GroupedLayerControl({}, self.feature_groups, radio).add_to(self.map)

    def getMap(self):
        return self.map

    def createGroup(self, name):
        self.feature_groups[name] = {}


class geojson():


    def __init__(self, baseMap, feature_group, name, data='None', shapefile=None, locationcol='Location'):
        self.baseMap = baseMap
        self.name = name
        self.vdict, self.vdict2 = {}, {}
        self.column1, self.column2 = None, None
        self.colormap = None
        self.colormap2 = None
        self.plotcolumns, self.plotlabels = [], []
        self.valuecolumns, self.valuestring = [], []
        self.locationcol = locationcol
        self.key = 'name'
        self.feature_group = feature_group
        if type(data) == str:
            if data == 'None':
                self.df = self.baseMap.df
            elif data[-4:] == '.csv':
                self.df = pd.read_csv('data')
            else:
                print("Enter path to a csv file.")
        else:
            self.df = data
        if shapefile == None:
            self.geodata = self.baseMap.geodata
        else:
            self.geodata = json.load(open(shapefile))
        self.baseMap.feature_groups[self.feature_group][self.name] = folium.map.FeatureGroup(name=name,
                                                                                             show=False).add_to(
            self.baseMap.map)

    def colorMap(self, column1, column2=None, threshold_min1=None, threshold_min2=None, threshold_max1=None,
                 threshold_max2=None):
        if threshold_min1 == None:
            threshold_min1 = self.df[column1].min()
            a = threshold_min1
        if threshold_max1 == None:
            threshold_max1 = self.df[column1].max()
        self.column1 = column1
        # self.colormap = LinearColormap(['#3f372f', '#62c1a6', '#bbf9d9', '#f2f2f2'],vmin=self.df[column1].min(),
        # vmax=self.df[column1].max()).to_step(data=self.df[column1], n=5, method='quantiles')
        self.colormap = LinearColormap(['#3f372f', '#1b424e', '#226b56', '#74aaa7', '#bbf9e9', '#ffffff'],
                                       vmin=self.df[self.df[column1] >= threshold_min1][column1].min(),
                                       vmax=self.df[self.df[column1] <= threshold_max1][column1].max()).to_step(
            data=self.df[(self.df[column1] <= threshold_max1) & (self.df[column1] >= threshold_min1)][column1], n=6, method='quantiles')

        # self.vdict =self.df.set_index(self.locationcol)[column1]
        self.vdict =self.df[(self.df[column1] <= threshold_max1) & (self.df[column1] >= threshold_min1)].set_index(self.locationcol)[column1]
        self.baseMap.map.add_child(self.colormap)
        self.baseMap.map.add_child(BindColormap(self.baseMap.feature_groups[self.feature_group][self.name], self.colormap))

        if column2 == None:
            self.colormap2 = None
        else:
            if threshold_min2 == None:
                threshold_min2 = self.df[column2].min()
            if threshold_max2 == None:
                threshold_max2 = self.df[column2].max()
            self.column2 = column2
            self.colormap2 = LinearColormap(['#3f372f', '#62c1a6', '#1b425e', '#bbf9d9', '#ffffff'],
                                            vmin=self.df[self.df[column2] >= threshold_min2][column2].min(),
                                            vmax=self.df[self.df[column2] <= threshold_max2][column2].max()).to_step(
                data=self.df[self.df[column2] <= threshold_max2][self.df[column2] >= 0][column2], n=5,
                method='quantiles')
            self.vdict2 = self.df[self.df[column2] <= threshold_max2][self.df[column2] >= threshold_min2].set_index(self.locationcol)[column2]
            self.baseMap.map.add_child(self.colormap2)
            self.baseMap.map.add_child(
                BindColormap(self.baseMap.feature_groups[self.feature_group][self.name], self.colormap2))

    def createMap(self, key='name'):
        self.key = key
        folium.GeoJson(self.geodata,
                       style_function=lambda feature: {
                           'fillColor': (
                               self.colormap(self.vdict[feature['properties'][self.key]]) if feature['properties'][
                                                                                                 self.key] in self.vdict else 'grey') if ~(
                                       self.column1 == None) else 'red',
                           'color': (
                               self.colormap2(self.vdict2[feature['properties'][self.key]]) if feature['properties'][
                                                                                                   self.key] in self.vdict2 else 'grey') if ~(
                                       self.column2 == None) else 'orange',
                           'weight': 2 if (self.column2 != None) else 0.5,
                           'fillOpacity': 1 if feature['properties'][self.key] in self.vdict else 0}).add_to(
            self.baseMap.feature_groups[self.feature_group][self.name])

    def addValue(self, columns, string):
        self.valuecolumns.append(columns)
        self.valuestring.append(string)

    def createPlots(self, columns, labels):
        self.plotcolumns.append(columns)
        self.plotlabels.append(labels)

    def copyInfoBox(self, geojson):
        self.valuecolumns = geojson.valuecolumns
        self.valuestring = geojson.valuestring
        self.plotcolumns = geojson.plotcolumns
        self.plotlabels = geojson.plotlabels

    def addInfoBox(self):

        for feature in self.geodata['features']:
            a = self.df[self.df["Location"] == feature['properties']['name']]
            ind = (a.index)[0]
            html = "<center><h2 style='font-family: Arial, Helvetica, sans-serif;'>" + feature['properties'][
                'name'] + "</h2></center><center>"
            for i in range(len(self.valuecolumns)):
                html += "<h4 style='font-family: Arial, Helvetica, sans-serif;'>" + str(
                    round(a.loc[ind][self.valuecolumns[i]] * 100, 2)) + "%" + self.valuestring[i] + "</h4>"
            encodedlist = []
            for i in range(len(self.plotcolumns)):
                fig1, ax1 = plt.subplots(figsize=(5, 3))
                ax1.pie([a.loc[(a.index)[0], j] for j in self.plotcolumns[i]], labels=self.plotlabels[i],
                        autopct='%1.1f%%', shadow=True, startangle=90)
                plt.savefig('myfig.png', transparent=True)
                encoded = b64encode(open('myfig.png', 'rb').read()).decode()
                encodedlist.append(encoded)
                html += '<img align="middle" src="data:image/png;base64,{}">'

            html += '</center>'

            geo = folium.GeoJson(feature['geometry'],
                                 style_function=lambda feature: {'weight': 0, 'fillOpacity': 0},
                                 tooltip=feature['properties']['name'])

            iframe = branca.element.IFrame(html=html.format(*encodedlist), width=400, height=400)
            folium.Popup(iframe).add_to(geo)
            geo.add_to(self.baseMap.feature_groups[self.feature_group][self.name])


class interestingFacts():
    def __init__(self, basemap, feature_group, name, locationcol='Location', data='None'):
        self.basemap = basemap
        self.name = name
        self.Loc = []
        self.tdict, self.pdict, self.pidict, self.hdict, self.cdict = {}, {}, {}, {}, {}
        self.feature_group = feature_group
        self.locationcol = locationcol
        if type(data) == str:
            if data == 'None':
                self.df = self.basemap.df
            elif data[-4:] == '.csv':
                self.df = pd.read_csv('data')
            else:
                print("Enter path to a csv file.")
        else:
            self.df = data
        self.basemap.feature_groups[self.feature_group][self.name] = folium.map.FeatureGroup(name=self.name,
                                                                                             show=True).add_to(
            self.basemap.map)

    def addFacts(self, array, labels, icon_map, icon_pop):
        df = self.df
        for i in range(len(array)):
            arr = [0] * len(array)
            a = df.loc[df[array[i]].idxmax(axis=1)]
            for j in range(len(array)):
                arr[j] = a[array[j]]
            fig1, ax1 = plt.subplots(figsize=(1.8, 1.8))
            ax1.pie(arr, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
            plt.savefig('myfig.png', transparent=True)
            html1 = '<center><img align="middle" src="data:image/png;base64,{}"></center>'
            encoded = b64encode(open(icon_pop, 'rb').read()).decode()
            encpie = b64encode(open('myfig.png', 'rb').read()).decode()
            ic = icon_map
            l = a[self.locationcol]
            latlong = a['LatLong']
            if l not in self.Loc:
                self.Loc.append(l)
                self.pdict[l], self.hdict[l], self.tdict[l], self.pidict[l], self.cdict[
                    l] = '<h4><center>' + l + '</center></h4>', '', [], [], 0
                self.tdict[l].append(encoded)
                self.pdict[l] += '<hr><center><p style="padding:0px 10px 0px 10px">' + l
                self.hdict[l] += html1
            self.pidict[l].append(encpie)
            self.cdict[l] += 1
            string = " highest percentage of " + labels[i] + "."
            self.pdict[
                l] += ' has the' + string + '</p></center><center><img align="middle" src="data:image/png;base64,{}"></center>'
            iframe = branca.element.IFrame(html=self.pdict[l].format(*self.pidict[l]), width=400,
                                           height=220 + self.cdict[l] * 50)
            folium.Marker([latlong.split(",")[0], latlong.split(",")[1]], popup=folium.Popup(iframe),
                          icon=folium.features.CustomIcon(ic, icon_size=(28, 30)),
                          tooltip=self.hdict[l].format(*self.tdict[l])).add_to(
                self.basemap.feature_groups[self.feature_group][self.name])

    def getLatLong(self, name):
        l = Nominatim(user_agent="my-application").geocode(name)
        if (l == None):
            return "%.2f, %.2f" % (0, 0)
        return "%.2f, %.2f" % (l.latitude, l.longitude)

    def LatLong(self, csv_name):
        self.df["LatLong"] = self.df[self.locationcol].apply(lambda x: getLatLong(x))
        self.df.to_csv(csv_name, index=False)