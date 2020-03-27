import pandas as pd
import numpy as np
from urllib.request import urlretrieve
import requests
import plotly.express as px
import country_converter as coco


# Pulls an updated lost of COVID-19 cases from JHU CSSE repo
def pullCovidData():

    print("Pulling COVID-19 data from the web...")
    global cases
    cases_URL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases.csv"
    urlretrieve(cases_URL, 'cases.csv')
    cases = pd.read_csv('cases.csv')
    print("COVID-19 data retrieved.")

# Pulls projected March temperature (in degrees Celcius) from the World Bank's Climate Data API
def pullTempData():

    print("Pulling temperature data from the web...")
    global countries

    # Using a set eliminates duplicate countries in our dataset
    countries = set(cases["Country_Region"])

    # Eliminating countries without a valid ISO3 code
    countries.discard("Cruise Ship")
    countries.discard("Holy See")
    countries.discard("Kosovo")
    countries.discard("Diamond Princess")

    # Declaring a dictionary that matches country to projected March temperature
    global country_to_temp
    country_to_temp = {}

    # Filling the dictionary with results from the World Bank API
    for country in countries:
        if country == "US":
            ISO = "usa"
            temp_URL = 'http://climatedataapi.worldbank.org/climateweb/rest/v1/country/mavg/tas/2020/2039/' + ISO.lower() + '.CSV'
            urlretrieve(temp_URL, 'temps.csv')
            temps = pd.read_csv('temps.csv')
            temp = temps.at[1, "Mar"]
            country_to_temp[country] = temp
        elif str(country) != 'nan':
            ISO = coco.convert(names = [country], to = 'ISO3')
            temp_URL = 'http://climatedataapi.worldbank.org/climateweb/rest/v1/country/mavg/tas/2020/2039/' + ISO.lower() + '.CSV'
            urlretrieve(temp_URL, 'temps.csv')
            temps = pd.read_csv('temps.csv')
            temp = temps.at[1, "Mar"]
            country_to_temp[country] = temp

    print("Temperature data retrieved.")

def tempAnalysis():

    print("Analyzing temperatures...")

    # Declaring a dataframe that stores temperature and corresponding number of COVID-19 cases
    global tempData
    tempData = pd.DataFrame(columns = ["temp", "numCases"])
    tempData.set_index('temp')

    #presetting TempData
    # - all temps equal to their temps
    # - all numCases equal to zero
    for country in countries:
        if str(country) != "nan":
            tempData.at[country_to_temp[country], "temp"] = country_to_temp[country]
            tempData.at[country_to_temp[country], "numCases"] = 0

    # Filling TempData with projected temperature and number of cases for each country
    for ind in cases.index:
        country = cases.at[ind, "Country_Region"]
        if country != "Holy See" and country != "Cruise Ship" and country != "Kosovo" and country != "Diamond Princess" and str(country) != "nan":
            temp = country_to_temp[country]
            tempData.at[temp, "numCases"] = tempData.at[temp, "numCases"] + cases.at[ind, "Confirmed"]

    print("Temperature analysis complete.")

# Cleaning data to make it more amenable to bar graph format
def aggregateTempData():

    # agTempData stores total number of confirmed cases in a range of temperature
    global agTempData
    agTempData = pd.DataFrame(columns = ["startTemp", "numCases"])
    agTempData.set_index("startTemp")

    # Initializing agTempData
    for i in range(-30, 31, 5):
        agTempData.at[i, "startTemp"] = i
        agTempData.at[i, "numCases"] = 0

    # Iterating through each temperature, populating agTempData
    for ind in tempData.index:
        agTempData.at[findStartTemp(ind), "numCases"] = agTempData.at[findStartTemp(ind), "numCases"] + tempData.at[ind, "numCases"]

# Given temperature, returns first temperature in the range the given temperature corresponds to
def findStartTemp(temp):
    for i in range(-30, 29, 5):
        if (temp - i >= 0 and temp - (i + 5) < 0):
            return i
    return 30

# Plots agTempData using plotly express
def plotTempData():
    print("Plotting temperature data...")
    fig = px.bar(agTempData, x = "startTemp", y = "numCases")
    fig.write_html("COVID-19_graphs.html")
    print("Graph generated.")

    # fig = px.scatter(x = tempData["temp"], y = tempData["numCases"], range_x = [-30, 30])
    # fig.write_html("COVID-19_graphs.html")

# Sorts data into a table with distance from equator, percentage of population that tested positive for COVID-19
def latitudeAnalysis():

    print("Sorting data by distance from equator...")
    global latData
    latData = pd.DataFrame(columns = ["distance", "numCases"])
    latData.set_index('distance')

    # Initializing latData
    for d in range(91):
        latData.at[d, "distance"] = d
        latData.at[d, 'numCases'] = 0


    for ind in cases.index:
        if (str(cases.at[ind, "Lat"]) != "nan"):
            dist = abs(int(cases["Lat"][ind]))
            if (0 <= dist) and (90 >= dist):
                latData.at[dist, "numCases"] = int(latData.at[dist, "numCases"]) + cases.at[ind, "Confirmed"]

    print("Sorting complete.")


# Plots latData using plotly express
def plotLatData():
    print("Plotting latitude data...")
    fig = px.scatter(latData, x = "distance", y = "numCases", range_x = [0, 90])
    fig.write_html("COVID-19_graphs.html")
    print("Graph generated.")

def main():

    pullCovidData()
    pullTempData()
    tempAnalysis()
    aggregateTempData()
    plotTempData()
    latitudeAnalysis()
    plotLatData()

if __name__ == '__main__':
    main()
