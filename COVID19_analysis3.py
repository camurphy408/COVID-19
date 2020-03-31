# Script for generating a scatterplot with x-axis corresponding to GDP per capita and y-axis corresponding to proportion of population diagnosed with coronavirus.
# Created by Claire Murphy, 3/30/20

import pandas as pd
import numpy as np
from urllib.request import urlretrieve
import requests
import plotly.express as px
import country_converter as coco
import json

# Pulls an updated list of COVID-19 cases from a JHU CSSE repo
def pullCovidData():

    print("Pulling COVID-19 data from the web...")
    global cases
    cases_URL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases.csv"
    urlretrieve(cases_URL, 'cases.csv')
    cases = pd.read_csv('cases.csv')
    print("COVID-19 data retrieved.")

# Created dataframe which will store population size, number of diagnosed COVID-19 cases, proportion of diagnosed COVID-19 cases, GDP, and GDP per capita for each country
def createDataFrame():

    print("Creating dataframe...")
    # Using a set eliminates duplicate countries in our dataset
    global countries
    countries = set(cases["Country_Region"])

    # Eliminating countries without a valid ISO3 code or countries that throw an error when we input it into the World Bank API
    countries.discard("Cruise Ship")
    countries.discard("Holy See")
    countries.discard("Kosovo")
    countries.discard("Diamond Princess")
    countries.discard("MS Zaandam")
    countries.discard("Taiwan*")
    countries.discard("Eritrea")
    countries.discard("Venezuela")
    countries.discard("Syria")

    # Creating the dataframe
    global countryData
    countryData = pd.DataFrame(columns = ["country", "population", "numCases", "density", "GPD", "perCapGDP"])
    for country in countries:
        if str(country) != "nan":
            countryData = countryData.append({'country' : country, "population" : 0, "numCases" : 0, "density" : 0, "GPD" : 0, "perCapGDP" : 0}, ignore_index=True)

    print("Dataframe created.")

# Pulls number of COVID-19 cases from our "cases" dataframe
# Pulls population size and GDP from World Bank API
def fillDataFrame():

    print("Filling data frame...")

    # Adds coronavirus cases to each country
    for ind in cases.index:
        country = cases.at[ind, 'Country_Region']
        # Making sure our "country" is one of the countries we can actually get data on...
        if country != "Holy See" and country != "Cruise Ship" and country != "Kosovo" and country != "Diamond Princess" and str(country) != "nan":
            countryData.loc[countryData["country"] == country, "numCases"] = cases.at[ind, "Confirmed"] + countryData.loc[countryData["country"] == country, "numCases"]

    # Adds population size and GDP to each country
    for ind in countryData.index:
        country = countryData.at[ind, "country"]
        if country == "US":
            ISO = "usa"
        else:
            ISO = coco.convert(names = [country], to = 'ISO3')

        # Adding population
        pop_url = "http://api.worldbank.org/v2/country/" + ISO.lower() + "/indicator/SP.POP.TOTL?date=2016&format=json"
        pop_response = requests.get(pop_url)
        pop_json = json.loads(pop_response.text)
        pop = pop_json[1][0]["value"]
        countryData.at[ind, "population"] = pop

        # Calculating proportion of population diagnosed with COVID-19
        countryData.at[ind, "density"] = float(countryData.at[ind, "numCases"]) / pop

        # Addding GDP
        GDP_url = "http://api.worldbank.org/v2/country/" + ISO.lower() + "/indicator/NY.GDP.MKTP.CD?date=2016&format=json"
        GDP_response = requests.get(GDP_url)
        GDP_json = json.loads(GDP_response.text)
        GDP = GDP_json[1][0]['value']
        countryData.at[ind, "GDP"] = GDP

        # Calculating GDP per capita
        countryData.at[ind, "perCapGDP"] = float(GDP) / pop

        # Updating user on status (this part of the code takes a while...)
        print(country, (35 - len(country)) * (" "), " (", str(ind + 1), "/", str(len(countryData.index)), ')')

    print("Data frame filled.")

# Plots countryData using plotly express
def plotCountryData():
    print("Plotting per capita GDP data...")
    labelsDict = { "perCapGDP" : "Per capita GDP (in US dollars)", "density" : "Proportion of population diagnosed with coronavirus"}
    fig = px.scatter(countryData, x = "perCapGDP", y = "density", hover_name = "country", labels = labelsDict)
    fig.write_html("COVID-19_graphs.html")
    print("Graph generated.")

def main():

    pullCovidData()
    createDataFrame()
    fillDataFrame()
    plotCountryData()

if __name__ == '__main__':
    main()
