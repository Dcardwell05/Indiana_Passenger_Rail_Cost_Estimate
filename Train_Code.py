"""
Course Number: ENGR 13300
Semester: e.g. Spring 2025

Description:
    Creating a program to calculate train costs.

Assignment Information:
    Assignment:     Individual Project
    Team ID:        001 - 18
    Author:         Daniel Cardwell, dcardwe@purdue.edu
    Date:           05/01/2025

Contributors:
    Name, login@purdue [repeat for each]

    My contributor(s) helped me:
    [ ] understand the assignment expectations without
        telling me how they will approach it.
    [ ] understand different ways to think about a solution
        without helping me plan my solution.
    [ ] think through the meaning of a specific error or
        bug present in my code without looking at my code.
    Note that if you helped somebody else with their code, you
    have to list that person as a contributor here as well.

Academic Integrity Statement:
    I have not used source code obtained from any unauthorized
    source, either modified or unmodified; nor have I provided
    another student access to my code.  The project I am
    submitting is my own original work.
"""

#Get Libraries
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString

def createline(start, end, citiesmap):

    #Get start and end coordinates
    scoord = citiesmap[citiesmap["municipalt"] == start].geometry.iloc[0].centroid
    ecoord = citiesmap[citiesmap["municipalt"] == end].geometry.iloc[0].centroid
    
    #Create line
    vectorline = LineString([scoord, ecoord])

    return vectorline

def terrainmap(citiesmap, vectorline):
    #Importing Physiography Natural Regions
    geo = gpd.read_file("DATAFILES/costphys.geojson")
    geo = geo.to_crs(epsg=26916)

    #Putting the vector in a GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=[vectorline], crs=citiesmap.crs)

    #Distance in each region
    dist_in_region = gpd.overlay(gdf, geo, how='intersection')

    dist_in_region["length"] = dist_in_region.length

    dist_per_region = dist_in_region.groupby("REGION").agg({
        "length": "sum",
        "COSTPERMILE": "first"  # or "mean" or "max" – if constant within each region, all will be same
    }).reset_index()

    return dist_per_region

def getrivers(vectorline):
    river_gdf = gpd.read_file("DATAFILES/RiverIN.geojson") # Getting river data
    river_gdf = river_gdf.to_crs(epsg=26916)
    
    #Get the rivers that intersect with the vector
    river_intersections = river_gdf[river_gdf.geometry.intersects(vectorline)]

    return len(river_intersections)

def getcost(dis_per_region, riverscount):
    #Cost per region
    dis_per_region["length_miles"] = dis_per_region["length"] / 1609.34 
    dis_per_region["segment_cost"] = dis_per_region["length_miles"] * dis_per_region["COSTPERMILE"]

    terrain_cost = dis_per_region["segment_cost"].sum()

    #Adding river cost
    river_cost = riverscount * 10000000

    total_cost = terrain_cost + river_cost

    total_cost = total_cost * 1.3 #30% increase

    #Printing all the costs
    print("\nCost per region:")
    for index, row in dis_per_region.iterrows():
        print(f"   {row['REGION']}: ${row['segment_cost']:,.2f}")
    print(f"River cost: ${river_cost:,.2f}")
    print(f"Contingency costs: ${.3 * (terrain_cost + river_cost):,.2f}")

    return total_cost

def main():
    #importing files
    citiesmap = gpd.read_file("DATAFILES/CensusCityBoundries.geojson")
    cities_geo = citiesmap["municipalt"].tolist()

    #Project the data to a coordinate system that uses meters
    citiesmap = citiesmap.to_crs(epsg=26916)
    cities_geo.sort()

    citiescsv = pd.read_csv("DATAFILES/Cities_FIPS.csv")
    citiescsv["Estimated Population (2020)"] = citiescsv["Estimated Population (2020)"].str.replace(",", "") #taking out commas
    citiescsv["Estimated Population (2020)"] = pd.to_numeric(citiescsv["Estimated Population (2020)"], errors='coerce') #coverting to numeric
    cities_pop = citiescsv[["Name", "Estimated Population (2020)"]]

    #Removing cities with population less than 30,000
    cities_pop = cities_pop[cities_pop["Estimated Population (2020)"] > 30000]

    #modifying amount of cities in citiesmap to be equal to cities_pop
    for i in range(len(cities_geo)-1, -1, -1): #Sort the cities by name
        if cities_geo[i] not in cities_pop["Name"].values:
            del cities_geo[i]

    citiesmap = citiesmap[citiesmap["municipalt"].isin(cities_geo)] 

    j = 0
    print("Cities with population greater than 30,000: ")
    for i in range(len(cities_geo)): #Display the list of cities for the user to choose from
        if ((j == 0) or ((j % 5) == 0)):
            print("\n")
        print(cities_geo[i], end=", ")
        j += 1
        
    start = input("\n\nInput your starting point city: ")
    while start not in cities_geo: #input validation
        print("Please enter a valid city name.")
        start = input("Input your starting point city: ")

    end = input("Input your ending point city: ")
    while (end not in cities_geo) or (end == start):
        print("Please enter a valid city name.")
        end = input("Input your ending point city: ")

    #Get distance vector
    vector = createline(start, end, citiesmap)

    distance = vector.length #Magnitude of the vector 

    distance_miles = distance / 1609.34 #Convert from meters to miles
    print(f"\nRailroad Length: {distance_miles:.2f} miles")

    #Get terrain cost data
    dis_per_region = terrainmap(citiesmap, vector)

    riverscount = getrivers(vector) # Getting the rivers count

    Cost = getcost(dis_per_region, riverscount) # Getting the cost

    print(f"\nTotal cost: $ {Cost:,.2f} ")

if __name__ == "__main__":
    main()