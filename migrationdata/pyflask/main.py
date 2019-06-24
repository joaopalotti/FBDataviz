from flask import Flask, request, render_template, render_template_string
import pandas as pd
import folium, json, mapping, simplifydf
from glob import glob
import plotmap, requests, os, base64
from matplotlib import pyplot as plt
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def index():
    countries = {}
    for i in glob('./static/??_dataframe*.csv.gz'):
        country_code = os.path.basename(i)[:2]
        countries[country_code] = mapping.convert_country_code(country_code)
    length = len(countries)

    # Sort list of countries by their names instead of by their code
    country_list = sorted(countries.items(), key=lambda x: x[1])
    li_path, li_country = zip(*country_list)
    return render_template("index.html", list_path=li_path, list_country=li_country, length=length)

@app.route('/country/<countrycode>', methods=['get','post'])
def country(countrycode):

    # img = io.BytesIO()
    country = mapping.convert_country_code(countrycode)
    # TODO: do not need a for here....
    for i in glob('static/{}_data*.csv.gz'.format(countrycode)):
        path = i
    df = pd.read_csv(path)
    df = simplifydf.simplify(df)
    df = df[df['citizenship'] != 'All'][df['citizenship'] != 'All Countries']
    fig, ax = plt.subplots(figsize=(9.5, 6))
    df.set_index('citizenship').sort_values('Total_mau', ascending=False).head(10)['Total_mau'].plot(kind='barh')
    ax.set_xlabel('', labelpad=15)
    ax.set_ylabel('', labelpad=30)
    plt.savefig('static/plotcountry{}.png'.format(countrycode), transparent=True)
    encoded = base64.b64encode(open('static/plotcountry{}.png'.format(countrycode).format(countrycode), 'rb').read()).decode()
    html1 = 'data:image/png;base64,{}'.format(encoded)
    os.remove('static/plotcountry{}.png'.format(countrycode))

    url = 'http://data.un.org/en/iso/{}.html'.format(countrycode)
    countryData = requests.get(url).text
    soup = BeautifulSoup(countryData)
    tables = soup.find_all("tbody")
    lists, i = [[], [], []], 1
    for tag in tables[1].find_all('td'):
        if i == 1:
            lists[0].append(tag.text)
        elif i == 2:
            lists[1].append(tag.text)
        elif i == 3:
            lists[2].append(tag.text)
        i = i + 1
        if i == 4:
            i = 1
    for index in range(2, 5):
        for tag in tables[index].find_all('td'):
            if i == 1:
                lists[0].append(tag.text)
            elif i == 2 | i == 3:
                pass
            elif i == 4:
                lists[2].append(tag.text)
            i = i + 1
            if i == 5:
                i = 1
    countrydf = pd.DataFrame(columns=['Attribute', 'Values'])
    countrydf['Attribute'], countrydf['Values'] = lists[0], lists[2]
    attribute=countrydf['Attribute'].tolist()
    value=countrydf['Values'].tolist()

    df = pd.read_csv(path)
    df = simplifydf.simplify(df)
    df = df[df['citizenship'] != 'All'][df['citizenship'] != 'Locals']
    fig, ax = plt.subplots(figsize=(9.5, 6))
    df.set_index('citizenship').sort_values('Total_mau', ascending=False).head(10)['Total_mau'].plot(kind='barh')
    ax.set_xlabel('', labelpad=15)
    ax.set_ylabel('', labelpad=30)
    plt.savefig('static/plotcountry{}-form.png'.format(countrycode), transparent=True)
    encoded = base64.b64encode(open('static/plotcountry{}-form.png'.format(countrycode), 'rb').read()).decode()
    html2 = 'data:image/png;base64,{}'.format(encoded)
    os.remove('static/plotcountry{}-form.png'.format(countrycode))

    if request.method == 'POST':

        #new barplot:
        if request.form.getlist('gender')[0]=='both':
            tempdf=maindf[maindf['genders']==0][maindf['ages_ranges']=="{u'min': 13}"]
        elif request.form.getlist('gender')[0]=='male':
            tempdf=maindf[maindf['genders']==1][maindf['ages_ranges']=="{u'min': 13}"]
        elif request.form.getlist('gender')[0]=='female':
            tempdf=maindf[maindf['genders']==2][maindf['ages_ranges']=="{u'min': 13}"]

        if request.form.getlist('scholarities')[0]=='all':
            tempdf=tempdf[tempdf['scholarities'].isnull()]
        elif request.form.getlist('scholarities')[0]=='graduated':
            tempdf=tempdf[tempdf['scholarities']=="{u'name': u'Graduated', u'or': [3, 7, 8, 9, 11]}"]
        elif request.form.getlist('scholarities')[0]=='nodegree':
            tempdf=tempdf[tempdf['scholarities']=="{u'name': u'No Degree', u'or': [1, 12, 13]}"]
        elif request.form.getlist('scholarities')[0]=='highschool':
            tempdf=tempdf[tempdf['scholarities']=="{u'name': u'High School', u'or': [2, 4, 5, 6, 10]}"]

        if request.form.getlist('os')[0]=='all':
            tempdf=tempdf[tempdf['access_device'].isnull()]
        elif request.form.getlist('os')[0]=='ios':
            tempdf=tempdf[tempdf['access_device']=="{u'or': [6004384041172], u'name': u'iOS'}"]
        elif request.form.getlist('os')[0] == 'android':
            tempdf = tempdf[tempdf['access_device'] == "{u'or': [6004386044572], u'name': u'Android'}"]
        elif request.form.getlist('os')[0] == 'others':
            tempdf = tempdf[tempdf['access_device'] == "{u'not': [6004384041172, 6004386044572], u'name': u'Other'}"]


        tempdf=tempdf[['citizenship', 'mau_audience']]
        tempdf = tempdf.dropna(subset=['citizenship'])


        for index, rows in tempdf.iterrows():
            if tempdf.citizenship[index] == "{u'not': [6015559470583], u'name': u'All - Expats'}":
                tempdf.citizenship[index] = "Locals"
            else:
                tempdf.citizenship[index] = tempdf.loc[index, 'citizenship'][
                                            tempdf.loc[index, 'citizenship'].find('(') + 1:tempdf.loc[index, 'citizenship'].find(
                                             ')')]
        tempdf = tempdf[tempdf['citizenship'] != 'Locals'][tempdf['citizenship'] != 'All']

        tempdf.set_index('citizenship').sort_values('mau_audience', ascending=False).head(10)['mau_audience'].plot(kind='barh')
        ax.set_xlabel('', labelpad=15)
        ax.set_ylabel('', labelpad=30)
        plt.savefig('static/plotcountry{}-form.png'.format(countrycode), transparent=True)
        encoded = base64.b64encode(open('static/plotcountry{}-form.png'.format(countrycode), 'rb').read()).decode()
        html2 = 'data:image/png;base64,{}'
        html2 = html2.format(encoded)
        os.remove('static/plotcountry{}-form.png'.format(countrycode))
        print(request.form.getlist('gender'))

        return render_template("countryinfo.html", cc=countrycode, country=country, attribute=attribute, value=value,
                               length=len(attribute), htmlstring1=html1, htmlstring2=html2)

    return render_template("countryinfo.html", cc=countrycode, country=country, attribute=attribute, value=value, length=len(attribute), htmlstring1=html1, htmlstring2=html2)

@app.route('/map/<countrycode>')
def map(countrycode):
    path = 'ok'
    for i in glob('static/{}_data*.csv.gz'.format(countrycode)):
        path = i
    df = pd.read_csv(path)
    df = simplifydf.simplify(df)
    bmap = plotmap.baseMap(data=df, shapefile='../places.geojson')
    bmap.createGroup('Gender')
    g = plotmap.geojson(bmap, 'Gender', 'Total', locationcol='citizenship')
    g.colorMap(column1='Total_dau', threshold_min1=0)
    g.createMap(key='name')

    g = plotmap.geojson(bmap, 'Gender', 'Male', locationcol='citizenship')
    g.colorMap(column1='Male_dau', threshold_min1=0)
    g.createMap(key='name')

    g = plotmap.geojson(bmap, 'Gender', 'Female', locationcol='citizenship')
    g.colorMap(column1='Female_dau', threshold_min1=0)
    g.createMap(key='name')
    folium.LayerControl().add_to(bmap.map)
    return render_template_string(bmap.map.get_root().render())


@app.route('/Qatar2')
def Qatar2():
    df = pd.read_csv('static/QatarMigration.csv')
    m = folium.Map(location=[0,0], zoom_start = 3)
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



if __name__ == "__main__":
    app.run(debug=True)
