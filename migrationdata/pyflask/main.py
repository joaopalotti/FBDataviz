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
    li_country = []
    li_path = []
    for i in glob('static/??_dataframe*.csv.gz'):
        li_country.append(mapping.convert_country_code(i[7:9]))
        li_path.append(i[7:9])
    length = len(li_country)
    return render_template("index.html", list_path=li_path, list_country=li_country, length=length)
    # return 'This is the homepage %s' % request.method

@app.route('/country/<countrycode>', methods=['get','post'])
def country(countrycode):

    # img = io.BytesIO()
    country = mapping.convert_country_code(countrycode)
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
    df = df[df['citizenship'] != 'All'][df['citizenship'] != 'All Countries']
    fig, ax = plt.subplots(figsize=(9.5, 6))
    # df.set_index('citizenship').sort_values('Total_mau', ascending=False).head(10)['Total_mau'].plot(kind='barh')
    # ax.set_xlabel('', labelpad=15)
    # ax.set_ylabel('', labelpad=30)
    plt.savefig('static/plotcountry{}-form.png'.format(countrycode), transparent=True)
    encoded = base64.b64encode(open('static/plotcountry{}-form.png'.format(countrycode), 'rb').read()).decode()
    html2 = 'data:image/png;base64,{}'.format(encoded)
    os.remove('static/plotcountry{}-form.png'.format(countrycode))

    if request.method == 'POST':
        df.set_index('citizenship').sort_values('Total_mau', ascending=False).head(10)['Total_mau'].plot(kind='barh')
        ax.set_xlabel('', labelpad=15)
        ax.set_ylabel('', labelpad=30)
        plt.savefig('static/plotcountry{}-form.png'.format(countrycode), transparent=True)
        encoded = base64.b64encode(open('static/plotcountry{}-form.png'.format(countrycode), 'rb').read()).decode()
        html2 = 'data:image/png;base64,{}'
        html2 = html2.format(encoded)
        os.remove('static/plotcountry{}-form.png'.format(countrycode))
        as_dict = request.form.getlist('myform')
        print(request.form.getlist('gender'))
        if request.form.getlist('gender')[0] == 'MaleFemale':
            print('check')
        return render_template("countryinfo.html", cc=countrycode, country=country, attribute=attribute, value=value,
                               length=len(attribute), htmlstring1=html1, htmlstring2=html2)

    return render_template("countryinfo.html", cc=countrycode, country=country, attribute=attribute, value=value,length=len(attribute),
                           htmlstring1=html1, htmlstring2=html2)


    # if request.method == 'POST':
    #     df.set_index('citizenship').sort_values('Total_mau', ascending=False).head(10)['Total_mau'].plot(kind='barh')
    #     ax.set_xlabel('', labelpad=15)
    #     ax.set_ylabel('', labelpad=30)
    #     plt.savefig('static/plotcountry{}-form.png'.format(countrycode), transparent=True)
    #     encoded = base64.b64encode(open('static/plotcountry{}-form.png'.format(countrycode), 'rb').read()).decode()
    #     html = 'data:image/png;base64,{}'
    #     html = html.format(encoded)
    #     return render_template("countryinfo.html",cc=countrycode,country=country,attribute=attribute,value=value,length=len(attribute), htmlstring=html)
    # img = io.BytesIO()
    # plt.savefig(img, format='png')
    # img.seek(0)
    # a = base64.b64encode(img.getvalue()).decode()
    # plt.close()
    # b = 'data:image/png;base64,{}'.format(a)

@app.route('/map/<countrycode>')
def map(countrycode):
    path = 'ok'
    for i in glob('static/{}_data*.csv.gz'.format(countrycode)):
        path = i
    df = pd.read_csv(path)
    df = simplifydf.simplify(df)
    bmap = plotmap.baseMap(data=df, shapefile='static/QatarMigration.geojson')
    bmap.createGroup('Gender')
    g = plotmap.geojson(bmap, 'Gender', 'Total', locationcol='citizenship')
    g.colorMap(column1='Total_dau', threshold_min1=0)
    g.createMap(key='citizenship')

    g = plotmap.geojson(bmap, 'Gender', 'Male', locationcol='citizenship')
    g.colorMap(column1='Male_dau', threshold_min1=0)
    g.createMap(key='citizenship')

    g = plotmap.geojson(bmap, 'Gender', 'Female', locationcol='citizenship')
    g.colorMap(column1='Female_dau', threshold_min1=0)
    g.createMap(key='citizenship')
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