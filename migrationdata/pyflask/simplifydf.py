import pandas as pd
import numpy as np
def simplify(df):
    collist = ['Other_dau', 'iOS_dau', 'Android_dau', 'Other_mau', 'iOS_mau', 'Android_mau',
              '13-14_dau', '15-19_dau', '15-24_dau', '20-24_dau', '25-29_dau', '30-34_dau', '35-39_dau', '40-44_dau',
              '45-49_dau', '50-54_dau', '55-59_dau', '25-64_dau', '60-64_dau', '13-nil_dau', '65-nil_dau',
              '13-14_mau', '15-19_mau', '15-24_mau', '20-24_mau', '25-29_mau', '30-34_mau', '35-39_mau', '40-44_mau',
              '45-49_mau', '50-54_mau', '55-59_mau', '25-64_mau', '60-64_mau', '13-nil_mau', '65-nil_mau',
              'Total_dau', 'Male_dau', 'Female_dau', 'Total_mau', 'Male_mau', 'Female_mau',
              'Graduated_dau', 'High_School_dau', 'No_Degree_dau', 'Graduated_mau', 'High_School_mau', 'No_Degree_mau']

    df = df[['access_device', 'ages_ranges', 'citizenship', 'genders', 'geo_locations', 'scholarities', 'dau_audience',
             'mau_audience']]
    df = df.dropna(subset=['access_device', 'ages_ranges', 'citizenship', 'genders', 'geo_locations', 'scholarities'])
    access_device_df = pd.pivot_table(df[df['ages_ranges'] == "{u'min': 13}"][df['genders'] == 0],
                                      values=['dau_audience', 'mau_audience'], index='citizenship',
                                      columns=['access_device'], aggfunc=np.sum, fill_value=-1)
    genders_df = pd.pivot_table(df[df['ages_ranges'] == "{u'min': 13}"], values=['dau_audience', 'mau_audience'],
                                index='citizenship', columns='genders', aggfunc=np.sum, fill_value=-1)
    ages_ranges_df = pd.pivot_table(df[df['genders'] == 0], values=['dau_audience', 'mau_audience'],
                                    index='citizenship', columns='ages_ranges', aggfunc=np.sum, fill_value=-1)
    scholarities_df = pd.pivot_table(df[df['ages_ranges'] == "{u'min': 13}"][df['genders'] == 0],
                                     values=['dau_audience', 'mau_audience'], index='citizenship',
                                     columns='scholarities', aggfunc=np.sum, fill_value=-1)
    cdf = pd.concat([access_device_df, ages_ranges_df, genders_df, scholarities_df], axis=1)
    cdf.columns = collist
    cdf = cdf.reset_index()
    for index, rows in cdf.iterrows():
        if cdf.citizenship[index] == "{u'not': [6015559470583], u'name': u'All - Expats'}":
            cdf.citizenship[index] = "All Countries"
        else:
            cdf.citizenship[index] = cdf.loc[index, 'citizenship'][
                                     cdf.loc[index, 'citizenship'].find('(') + 1:cdf.loc[index, 'citizenship'].find(')')]
    return cdf