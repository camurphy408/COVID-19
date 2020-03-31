# Script for generating bar graphs and scatterplots, with x-axis corresponding to temperature and y-axis corresponding to proportion of population diagnosed with coronavirus.
# Created by Claire Murphy, 3/27/20

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

# Created dataframe which will store average March temperature, population, and number of diagnosed COVID-19 cases for each country
def createDataFrame():

    print("Creating dataframe...")
    # Using a set eliminates duplicate countries in our dataset
    global countries
    countries = set(cases["Country_Region"])

    # Eliminating countries without a valid ISO3 code
    countries.discard("Cruise Ship")
    countries.discard("Holy See")
    countries.discard("Kosovo")
    countries.discard("Diamond Princess")
    countries.discard("MS Zaandam")

    # Creating the dataframe
    global countryData
    countryData = pd.DataFrame(columns = ["country", "temp", "population", "numCases"])
    for country in countries:
        if str(country) != "nan":
            countryData = countryData.append({'country' : country, 'temp' : 0, 'population' : 0, 'numCases' : 0}, ignore_index=True)

    print("Dataframe created.")

# Pulls projected March temperature (in degrees Celcius) from the World Bank's Climate Data API
# Pulls population size from REST Countries API
# Pulls number of COVID-19 cases from our "cases" dataframe
def fillDataFrame():

    print("Filling data frame...")

    for ind in countryData.index:
        country = countryData.at[ind, "country"]
        if country == "US":
            ISO = "usa"
        else:
            ISO = coco.convert(names = [country], to = 'ISO3')

        # Retrieving average March temperature
        temp_URL = 'http://climatedataapi.worldbank.org/climateweb/rest/v1/country/mavg/tas/2020/2039/' + ISO.lower() + '.CSV'
        urlretrieve(temp_URL, 'temps.csv')
        temps = pd.read_csv('temps.csv')
        temp = temps.at[1, "Mar"]
        countryData.at[ind, "temp"] = temp

        # Retrieving population size from REST Countries API
        pop_URL = "https://restcountries.eu/rest/v2/alpha/" + ISO.lower()
        r = requests.get(pop_URL)
        country_info = json.loads(r.text)
        pop = country_info["population"]
        countryData.at[ind, "population"] = pop

        # Updating user on status (this part of the code takes a while...)
        print(countryData.at[ind, "country"], " ", countryData.at[ind, "temp"], " ", countryData.at[ind, "population"], " (", str(ind + 1), "/", str(len(countryData.index)), ')')

    # Adds coronavirus cases to each country
    for ind in cases.index:
        country = cases.at[ind, 'Country_Region']
        # Making sure our "country" is one of the countries we can actually get data on...
        if country != "Holy See" and country != "Cruise Ship" and country != "Kosovo" and country != "Diamond Princess" and str(country) != "nan":
            countryData.loc[countryData["country"] == country, "numCases"] = cases.at[ind, "Confirmed"] + countryData.loc[countryData["country"] == country, "numCases"]

    print("Data frame filled.")

# Calculates proportion of COVID-19 cases for each temperature range
def barTempAnalysis():

    # barTempData stores total number of confirmed cases in a range of temperatures
    global barTempData
    barTempData = pd.DataFrame(columns = ["temp", "numCases", "totalPop", "density"])
    for i in range(-30, 31, 5):
        barTempData = barTempData.append({'temp' : i, 'numCases' : 0, 'totalPop' : 0, 'density' : 0}, ignore_index=True)

    # Iterates through each country, adding COVID-19 cases and population to the correct temperature range
    for ind in countryData.index:
        startTemp = findStartTemp(countryData.at[ind, "temp"])
        barTempData.loc[barTempData["temp"] == startTemp, "numCases"] = barTempData.loc[barTempData["temp"] == startTemp, "numCases"] + countryData.at[ind, "numCases"]
        barTempData.loc[barTempData["temp"] == startTemp, "totalPop"] = barTempData.loc[barTempData["temp"] == startTemp, "totalPop"] + countryData.at[ind, "population"]

    # Calculated density for each temperature range
    for i in range(-25, 29, 5):
        barTempData.loc[barTempData["temp"] == i, "density"] = float(barTempData.loc[barTempData["temp"] == i, "numCases"]) / barTempData.loc[barTempData["temp"] == i, "totalPop"]


# Given temperature, returns first temperature in the range the given temperature corresponds to
def findStartTemp(temp):
    for i in range(-30, 29, 5):
        if (temp - i >= 0 and temp - (i + 5) < 0):
            return i
    return 30

# Plots barTempData using plotly express
def plotBarTempData():
    print("Plotting temperature data...")
    fig = px.bar(barTempData, x = "temp", y = "density", labels = { "temp" : "Average March temperature (in degrees Celcius)", "density" : "Proportion of population diagnosed with coronavirus"})
    fig.write_html("COVID-19_graphs.html")
    print("Graph generated.")

# Calculates proportion of individuals diagnosed with COVID-19 for each temperature
def scatTempAnalysis():

    # scatTempData stores total number of confirmed cases in a range of temperature
    global scatTempData
    scatTempData = pd.DataFrame(columns = ["temp", "numCases", "totalPop", "density"])
    for i in range(-30, 31):
        scatTempData = scatTempData.append({'temp' : i, 'numCases' : 0, 'totalPop' : 0, 'density' : 0}, ignore_index=True)

    # Iterates through each country, adding numCases and population to the correct temperature
    for ind in countryData.index:
        startTemp = round(countryData.at[ind, "temp"])
        scatTempData.loc[scatTempData["temp"] == startTemp, "numCases"] = scatTempData.loc[scatTempData["temp"] == startTemp, "numCases"] + countryData.at[ind, "numCases"]
        scatTempData.loc[scatTempData["temp"] == startTemp, "totalPop"] = scatTempData.loc[scatTempData["temp"] == startTemp, "totalPop"] + countryData.at[ind, "population"]

    # Calculating density
    for i in range(-22, 29):
        # Avoiding division by zero (population of zero for certain temperatures)
        if (i == -22 or i == -19 or i == -13 or (i >= -10 and i != -4)):
            scatTempData.loc[scatTempData["temp"] == i, "density"] = float(scatTempData.loc[scatTempData["temp"] == i, "numCases"]) / scatTempData.loc[scatTempData["temp"] == i, "totalPop"]

# Plots scatTempData using plotly express
def plotScatTempData():
    print("Plotting temperature data...")
    fig = px.scatter(scatTempData, x = "temp", y = "density", labels = { "temp" : "Average March temperature (in degrees Celcius)", "density" : "Proportion of population diagnosed with coronavirus"})
    fig.write_html("COVID-19_graphs.html")
    print("Graph generated.")

def main():

    pullCovidData()
    createDataFrame()
    fillDataFrame()
    scatTempAnalysis()
    plotScatTempData()
    # barTempAnalysis()
    # plotBarTempData()

if __name__ == '__main__':
    main()
