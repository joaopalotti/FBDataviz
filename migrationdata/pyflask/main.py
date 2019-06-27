from flask import Flask, request, render_template, render_template_string
import pandas as pd
from glob import glob
import folium
import json
import requests
import os
import base64
from matplotlib import pyplot as plt
from bs4 import BeautifulSoup

# My functions
import plotmap
import mapping
import mapnavbar

app = Flask(__name__)

@app.route('/')
def index():
    countries = {}
    for i in glob('./static/original/??_dataframe*.csv.gz'):
        country_code = os.path.basename(i)[:2]
        countries[country_code] = mapping.convert_country_code(country_code)
    length = len(countries)

    # Sort list of countries by their names instead of by their code
    country_list = sorted(countries.items(), key=lambda x: x[1])
    li_path, li_country = zip(*country_list)
    return render_template("index.html", list_path=li_path, list_country=li_country, length=length)


@app.route('/plotgraph')
def plotgraph():
    gender = request.args.get('gender')
    scholarities = request.args.get('scholarities')
    os_var = request.args.get('os')
    countrycode = request.args.get('cc')
    path = glob('./static/original/%s_dataframe_collected_finished_*.csv.gz' % (countrycode))[0]
    maindf = pd.read_csv(path)

    if gender == 'both':
        tempdf = maindf[(maindf['genders'] == 0) & (maindf['ages_ranges'] == "{u'min': 13}")]
    elif gender == 'male':
        tempdf = maindf[(maindf['genders'] == 1) & (maindf['ages_ranges'] == "{u'min': 13}")]
    elif gender == 'female':
        tempdf = maindf[(maindf['genders'] == 2) & (maindf['ages_ranges'] == "{u'min': 13}")]

    if scholarities == 'all':
        tempdf = tempdf[tempdf['scholarities'].isnull()]
    elif scholarities == 'graduated':
        tempdf = tempdf[tempdf['scholarities'] == "{u'name': u'Graduated', u'or': [3, 7, 8, 9, 11]}"]
    elif scholarities == 'nodegree':
        tempdf = tempdf[tempdf['scholarities'] == "{u'name': u'No Degree', u'or': [1, 12, 13]}"]
    elif scholarities == 'highschool':
        tempdf = tempdf[tempdf['scholarities'] == "{u'name': u'High School', u'or': [2, 4, 5, 6, 10]}"]

    if os_var == 'all':
        tempdf = tempdf[tempdf['access_device'].isnull()]
    elif os_var == 'ios':
        tempdf = tempdf[tempdf['access_device'] == "{u'or': [6004384041172], u'name': u'iOS'}"]
    elif os_var == 'android':
        tempdf = tempdf[tempdf['access_device'] == "{u'or': [6004386044572], u'name': u'Android'}"]
    elif os_var == 'others':
        tempdf = tempdf[tempdf['access_device'] == "{u'not': [6004384041172, 6004386044572], u'name': u'Other'}"]

    tempdf = tempdf[['citizenship', 'mau_audience']]
    tempdf = tempdf.dropna(subset=['citizenship'])


    for index, rows in tempdf.iterrows():
        if tempdf.citizenship[index] == "{u'not': [6015559470583], u'name': u'All - Expats'}":
            tempdf.citizenship[index] = "Locals"
        else:
            tempdf.citizenship[index] = tempdf.loc[index, 'citizenship'][
                                        tempdf.loc[index, 'citizenship'].find('(') + 1:tempdf.loc[
                                            index, 'citizenship'].find(
                                            ')')]
    tempdf = tempdf[tempdf['citizenship'].apply(lambda x: x not in set(['All', 'Locals']))]
    fig, ax = plt.subplots(figsize=(9.5, 6))
    if tempdf[tempdf['mau_audience'] > 1000].empty:
        plothtml = ""
    else:
        tempdf[tempdf['mau_audience'] > 1000].set_index('citizenship').sort_values('mau_audience', ascending=False).head(10)[::-1]['mau_audience'].plot(kind='barh')
        ax.set_xlabel('', labelpad=15)
        ax.set_ylabel('', labelpad=30)
        plt.savefig('static/plot.png', transparent=True)
        encoded = base64.b64encode(open('static/plot.png', 'rb').read()).decode()
        plothtml = 'data:image/png;base64,{}'
        plothtml = plothtml.format(encoded)
        os.remove('static/plot.png')

    return render_template('plotgraph.html', plot=plothtml, gender=gender, scholarities=scholarities, os=os_var)

@app.route('/plotpie')
def plotpie():
    location = request.args.get('location')
    category = request.args.get('category')
    countrycode = request.args.get('cc')
    path = glob('static/simplified/{}.csv.gz'.format(countrycode))[0]
    maindf = pd.read_csv(path)
    df=maindf.head(2)
    fig, ax = plt.subplots(figsize=(9.5, 6))

    if category=='Gender':
        if location=='All':
            male=df.loc[1]['Male_mau']
            female=df.loc[1]['Female_mau']
        if location=='Local':
            male=df.loc[0]['Male_mau']
            female=df.loc[0]['Female_mau']
        else:
            male=df.loc[1]['Male_mau']-df.loc[0]['Male_mau']
            female=df.loc[1]['Female_mau']-df.loc[0]['Female_mau']
        ax.pie([male,female], labels=['male', 'female'], autopct='%1.1f%%', shadow=True, startangle=90)
        plt.savefig('myfig.png', transparent = True)
        encoded = b64encode(open('myfig.png', 'rb').read()).decode()

    if category=='Education':
        if location=='All':
            Graduated=df.loc[1]['Graduated_mau']
            High_School=df.loc[1]['High_School_mau']
            No_Degree=df.loc[1]['No_Degree_mau']
        if location=='Local':
            Graduated=df.loc[0]['Graduated_mau']
            High_School=df.loc[0]['High_School_mau']
            No_Degree=df.loc[0]['No_Degree_mau']
        else:
            Graduated=df.loc[1]['Graduated_mau']-df.loc[0]['Graduated_mau']
            High_School=df.loc[1]['High_School_mau']-df.loc[0]['High_School_mau']
            No_Degree=df.loc[1]['No_Degree_mau']-df.loc[0]['No_Degree_mau']
        ax.pie([Graduated,High_School, No_Degree], labels=['Graduated', 'High_School', 'No_Degree'], autopct='%1.1f%%', shadow=True, startangle=90)
        plt.savefig('myfig.png', transparent = True)
        encoded = b64encode(open('myfig.png', 'rb').read()).decode()
            
    if category=='OS':
        if location=='All':
            other=df.loc[1]['Other_mau']
            ios=df.loc[1]['iOS_mau']
            android=df.loc[1]['Android_mau']
        if location=='Local':
            other=df.loc[0]['Other_mau']
            ios=df.loc[0]['iOS_mau']
            android=df.loc[0]['Android_mau']
        else:
            other=df.loc[1]['Other_mau']-df.loc[0]['Other_mau']
            ios=df.loc[1]['iOS_mau']-df.loc[0]['iOS_mau']
            android=df.loc[1]['Android_mau']-df.loc[0]['Android_mau']
        ax.pie([other,ios, android], labels=['other', 'ios', 'android'], autopct='%1.1f%%', shadow=True, startangle=90)
        plt.savefig('myfig.png', transparent = True)
        encoded = b64encode(open('myfig.png', 'rb').read()).decode()
        

    piehtml = 'data:image/png;base64,{}'
    piehtml = pietml.format(encoded)
    os.remove('myfig.png')

    return render_template('plotpie.html', pie=piehtml, location=location, category=category)



#Using this function to remove the characters in the end
#Can we alternatively use re?
def isdigit2(inputString):
    return any(char.isdigit() for char in inputString)

@app.route('/country/<countrycode>', methods=['get','post'])
def country(countrycode):

    country = mapping.convert_country_code(countrycode)
    path = glob('static/simplified/{}.csv.gz'.format(countrycode))[0]

    df = pd.read_csv(path)
    df = df[df['citizenship'].apply(lambda x: x not in set(['All', 'Locals']))]

    print(df.columns)
    fig, ax = plt.subplots(figsize=(9.5, 6))
    df[df['Total_mau']>1000].set_index('citizenship').sort_values('Total_mau', ascending=False).head(10)['Total_mau'][::-1].plot(kind='barh')

    ax.set_xlabel('', labelpad=15)
    ax.set_ylabel('', labelpad=30)

    plt.savefig('static/plotcountry1{}.png'.format(countrycode), transparent=True)
    encoded = base64.b64encode(open('static/plotcountry1{}.png'.format(countrycode), 'rb').read()).decode()
    html1 = 'data:image/png;base64,{}'.format(encoded)
    os.remove('static/plotcountry1{}.png'.format(countrycode))

    fig, ax = plt.subplots(figsize=(9.5, 6))

    male=10
    female=10
    ax.pie([male,female], labels=['male', 'female'], autopct='%1.1f%%', shadow=True, startangle=90)
    plt.savefig('myfig.png', transparent = True)
    encoded = base64.b64encode(open('myfig.png', 'rb').read()).decode()
    html2 = 'data:image/png;base64,{}'.format(encoded)
    os.remove('myfig.png')


    url = 'http://data.un.org/en/iso/{}.html'.format(countrycode)
    countryData = requests.get(url).text
    soup = BeautifulSoup(countryData)
    tables = soup.find_all("tbody")
    lists, i = [[], []], 1
    for tag in tables[1].find_all('td'):
        if i == 1:
            lists[0].append(tag.text)
        elif i == 3:
            text = tag.text
            if ((isdigit2(text))&(text[1:].find('-')==-1)):
                text = text.replace('a', '').replace('b', '').replace('c', '').replace('d', '').replace('e','').replace('f', '').replace('g', '').replace(',','').replace(' ', '')
            lists[1].append(text)
        i += 1
        if i == 4:
            i = 1
    for index in range(2, 5):
        for tag in tables[index].find_all('td'):
            if i == 1:
                lists[0].append(tag.text)
            elif i == 4:
                text = tag.text
                if (isdigit2(text)):
                    text = text.replace('a', '').replace('b', '').replace('c', '').replace('d', '').replace('e','').replace('f', '').replace('g', '').replace(',', '').replace(' ', '')
                lists[1].append(text)
            i += 1
            if i == 5:
                i = 1
    attribute, value = lists[0], lists[1]
    return render_template("countryinfo.html", cc=countrycode, country=country, attribute=attribute, value=value, length=len(attribute), htmlstring1=html1, htmlstring2=html1, htmlstring3=html2)

@app.route('/map/<countrycode>')
def map(countrycode):
    path = glob('./static/simplified/{}.csv.gz'.format(countrycode))[0]
    df = pd.read_csv(path)

    bmap = plotmap.BaseMap(data=df, shapefile='../places.geojson')
    bmap.createGroup('Gender')
    g = plotmap.Geojson(bmap, 'Gender', 'Total', locationcol='citizenship')
    g.colorMap(column1='Total_mau')
    #g.colorMap(column1='Total_mau', threshold_min1=1001)
    g.createMap(key='name')

    g.addValue(["Male_mau", "Female_mau"], " of the population are males")
    g.addValue(['Female_mau', "Male_mau", ], " of the population are females")

    g.addValue(["Other_mau", "iOS_mau", "Android_mau"], " of the population are using other operating system")
    g.addValue(["iOS_mau", "Other_mau", "Android_mau"], " of the population are using iOS operating system")
    g.addValue(["Android_mau", "iOS_mau", "Other_mau"], " of the population are using Android operating system")

    g.addValue(["No_Degree_mau", "Graduated_mau", "High_School_mau"], " of the population do not have a degree")
    g.addValue(["Graduated_mau", "High_School_mau", "No_Degree_mau"], " of the population graduated from college")
    g.addValue(["High_School_mau", "Graduated_mau", "No_Degree_mau"], " of the population have a high school degree")
    g.addInfoBox(countrycode)
   
    g = plotmap.Geojson(bmap, 'Gender', 'Male', locationcol='citizenship')
    g.colorMap(column1='Male_mau')
    #g.colorMap(column1='Male_mau', threshold_min1=1001)
    g.createMap(key='name')

    g.addValue(["Male_mau", "Female_mau"], " of the population are males")
    g.addValue(['Female_mau', "Male_mau", ], " of the population are females")

    g.addValue(["Other_mau", "iOS_mau", "Android_mau"], " of the population are using other operating system")
    g.addValue(["iOS_mau", "Other_mau", "Android_mau"], " of the population are using iOS operating system")
    g.addValue(["Android_mau", "iOS_mau", "Other_mau"], " of the population are using Android operating system")

    g.addValue(["No_Degree_mau", "Graduated_mau", "High_School_mau"], " of the population do not have a degree")
    g.addValue(["Graduated_mau", "High_School_mau", "No_Degree_mau"], " of the population graduated from college")
    g.addValue(["High_School_mau", "Graduated_mau", "No_Degree_mau"], " of the population have a high school degree")

    g.addInfoBox(countrycode)

    g = plotmap.Geojson(bmap, 'Gender', 'Female', locationcol='citizenship')
    g.colorMap(column1='Female_mau')
    #g.colorMap(column1='Female_dau', threshold_min1=1001)
    g.createMap(key='name')

    g.addValue(["Male_mau", "Female_mau"], " of the population are males")
    g.addValue(['Female_mau', "Male_mau", ], " of the population are females")

    g.addValue(["Other_mau", "iOS_mau", "Android_mau"], " of the population are using other operating system")
    g.addValue(["iOS_mau", "Other_mau", "Android_mau"], " of the population are using iOS operating system")
    g.addValue(["Android_mau", "iOS_mau", "Other_mau"], " of the population are using Android operating system")

    g.addValue(["No_Degree_mau", "Graduated_mau", "High_School_mau"], " of the population do not have a degree")
    g.addValue(["Graduated_mau", "High_School_mau", "No_Degree_mau"], " of the population graduated from college")
    g.addValue(["High_School_mau", "Graduated_mau", "No_Degree_mau"], " of the population have a high school degree")

    g.addInfoBox(countrycode)

    '''bmap.createGroup('Facts')
    f= plotmap.interestingFacts(bmap, 'Facts', 'interesting fact', 'citizenship')
    f.addFacts(['Total_mau', 'Other_mau', 'iOS_mau', 'Android_mau'], ('Other', 'iOS', 'Android'),'trophy.png', 'phone.png')

    bmap.groupedLayerControl(['Gender','Facts'])'''
    folium.LayerControl().add_to(bmap.map)
    # bmap.map = mapnavbar.addNavBar(bmap.map)
    mapnavbar.FloatImage().add_to(bmap.map)
    # bmap.map.save(os.path.join('results', 'FloatImage.html'))
    return render_template_string(bmap.map.get_root().render())


@app.route('/Qatar2')
def Qatar2():
    df = pd.read_csv('static/QatarMigration.csv')
    m = folium.Map(location=[0, 0], zoom_start=3)
    vdict = df[df['Total_dau'] >= 0].set_index('citizenship')['Total_dau']
    geodata = json.load(open('static/QatarMigration.geojson'))
    folium.GeoJson(geodata,
                   style_function=lambda feature: {
                       'fillColor': 'cyan' if feature['properties']['citizenship'] in vdict else 'grey',
                       'color': 'black' if feature['properties']['citizenship'] in vdict else 'grey',
                       'weight': 1,
                       'fillOpacity': 1 if feature['properties']['citizenship'] in vdict else 0},
                   tooltip=folium.features.GeoJsonTooltip(fields=['citizenship'],
                                                          labels=False,
                                                          sticky=False)).add_to(m)
    m.save('templates/Country.html')
    return render_template("Country.html")


@app.route('/about')
def about():
    return render_template("about.html")
if __name__ == "__main__":
    app.run(debug=True)
