import pandas as pd
import numpy as np
import os

def gather_season(data, season):
    if season=="winter":
        return data.loc[data.month.isin([12, 1, 2]), :]
    elif season=="spring":
        return data.loc[data.month.isin([3, 4, 5]), :]
    elif season=="summer":
        return data.loc[data.month.isin([6, 7, 8]), :]
    elif season=="fall":
        return data.loc[data.month.isin([9, 10, 11]), :]

def season_month(season):
    if season=="winter":
        return [12, 1, 2]
    elif season=="spring":
        return [3, 4, 5]
    elif season=="summer":
        return [6, 7, 8]
    elif season=="fall":
        return [9, 10, 11]

def year_month_filter(data, sample_year, sample_month):
    data = data.loc[data.year.isin([sample_year]), :]
    data = data.loc[data.month.isin([sample_month]), :]
    return data

def remove_time_index(data):
    data = data.reset_index(drop=True)
    data = data.drop(['time', 'year', 'month', 'dayofweek', 'hour'], axis=1)
    return data


def filter_sample_year(data, sample_year):
    data["time"] = pd.to_datetime(data["time"])
    data['year'] = data['time'].dt.year
    data['month'] = data['time'].dt.month
    data['hour'] = data['time'].dt.hour
    data['dayofweek'] = data['time'].dt.dayofweek
    if sample_year != None:
        data = data.loc[data.year.isin(sample_year), :]
    return data

def make_datetime(data, time_format):
    data["time"] = pd.to_datetime(data["time"],
                                  format=time_format,
                                  exact=False)
    data['year'] = data['time'].dt.year
    data['month'] = data['time'].dt.month
    data['hour'] = data['time'].dt.hour
    data['dayofweek'] = data['time'].dt.dayofweek
    return data

def gather_regular_sample(data, season, seasons, regularSeasonHours,
                          sample_hour):
    # data = gather_season(data=data, season=season)
    data = data.reset_index(drop=True)
    sample_data = data.iloc[sample_hour:sample_hour + regularSeasonHours,:]
    
    # Sort sample_data to start on midnight monday
    sample_data = sample_data.sort_values(by=['dayofweek','hour'])
    
    # Drop non-country columns
    sample_data = remove_time_index(sample_data)
    
    hours = list(range(1 + regularSeasonHours * seasons.index(season),
                       regularSeasonHours * (seasons.index(season) + 1) + 1))
    return [sample_data, hours]

def sample_generator(data, regularSeasonHours, scenario, season, seasons,
                     period, generator, sample_hour):
    [sample_data, hours] = gather_regular_sample(data, season, seasons,
                                                 regularSeasonHours,
                                                 sample_hour)
    generator_data = pd.DataFrame()
    if generator=='Windoffshoregrounded' or generator=='Windoffshorefloating':
        startNOnode = 2
    else:
        startNOnode = 1
    for c in sample_data.columns:
        if c == "NO":
            for i in range(startNOnode, 6):
                c_no = c + str(i)
                df = pd.DataFrame(
                    data={'Node': c_no, "IntermitentGenerators": generator,
                          "Operationalhour": hours,
                          "Scenario": "scenario" + str(scenario),
                          "Period": period,
                          "GeneratorStochasticAvailabilityRaw": 
                              sample_data[c].values})
                generator_data = pd.concat([generator_data,df], ignore_index=True)
        else:
            df = pd.DataFrame(
                data={'Node': c, "IntermitentGenerators": generator,
                      "Operationalhour": hours,
                      "Scenario": "scenario" + str(scenario),
                      "Period": period,
                      "GeneratorStochasticAvailabilityRaw": 
                          sample_data[c].values})
            generator_data = pd.concat([generator_data,df], ignore_index=True)
    return generator_data

def sample_hydro(data, regularSeasonHours, scenario, season,
                 seasons, period, sample_hour):
    [sample_data, hours] = gather_regular_sample(data, season, seasons,
                                                 regularSeasonHours,
                                                 sample_hour)
    hydro_data = pd.DataFrame()
    for c in sample_data.columns:
        if c != 'time':
            df = pd.DataFrame(
                data={'Node': c, "Period": period, "Season": season,
                      "Operationalhour": hours, 
                      "Scenario": "scenario" + str(scenario),
                      "HydroGeneratorMaxSeasonalProduction": 
                          sample_data[c].values})
            hydro_data = pd.concat([hydro_data,df], ignore_index=True)
    return hydro_data

def sample_load(data, regularSeasonHours, scenario, season, seasons,
                period, sample_hour):
    [sample_data, hours] = gather_regular_sample(data, season, seasons,
                                                 regularSeasonHours,
                                                 sample_hour)
    load = pd.DataFrame()
    for c in sample_data.columns:
        if c != 'time':
            df = pd.DataFrame(
                data={'Node': c, "Period": period, "Operationalhour": hours,
                      "Scenario": "scenario" + str(scenario),
                      "ElectricLoadRaw_in_MW": sample_data[c].values})
            load = pd.concat([load,df], ignore_index=True)
    return load

def gather_peak_sample(data, seasons, regularSeasonHours, peakSeasonHours,
                       country_sample, overall_sample):
    data = data.reset_index(drop=True)
    country_peak = data.iloc[
        int(country_sample - (peakSeasonHours/2)):int(
            country_sample + (peakSeasonHours/2)),
        :]
    overall_peak = data.iloc[
        int(overall_sample - (peakSeasonHours/2)):int(
            overall_sample + (peakSeasonHours/2)),
        :]
    
    # Sort data to start on midnight 
    country_peak = country_peak.sort_values(by=['hour'])
    overall_peak = overall_peak.sort_values(by=['hour'])
    
    # Drop non-country columns
    country_peak = remove_time_index(country_peak)
    overall_peak = remove_time_index(overall_peak)
    
    country_hours = list(
        range(1 + regularSeasonHours * len(seasons),
              regularSeasonHours * len(seasons) + peakSeasonHours + 1)
        )
    overall_hours = list(
        range(1 + regularSeasonHours * len(seasons) + peakSeasonHours,
              regularSeasonHours * len(seasons) + 2 * peakSeasonHours + 1)
        )
    return [country_peak, overall_peak, country_hours, overall_hours]

def sample_hydro_peak(data, seasons, scenario, period, regularSeasonHours,
                      peakSeasonHours, overall_sample, country_sample):
    peak_data = pd.DataFrame()
    [country_peak, overall_peak,
     country_hours, overall_hours] = gather_peak_sample(data, seasons,
                                                        regularSeasonHours,
                                                        peakSeasonHours,
                                                        country_sample,
                                                        overall_sample)
    for c in country_peak.columns:
        df = pd.DataFrame(
            data={'Node': c, "Period": period, "Season": "peak1",
                  "Operationalhour": country_hours,
                  "Scenario": "scenario" + str(scenario),
                  "HydroGeneratorMaxSeasonalProduction": 
                      country_peak[c].values})
        peak_data = pd.concat([peak_data,df], ignore_index=True)
        df = pd.DataFrame(
            data={'Node': c, "Period": period, "Season": "peak2",
                  "Operationalhour": overall_hours,
                  "Scenario": "scenario" + str(scenario),
                  "HydroGeneratorMaxSeasonalProduction": 
                      overall_peak[c].values})
        peak_data = pd.concat([peak_data,df], ignore_index=True)
    return peak_data

def sample_load_peak(data, seasons, scenario, period, regularSeasonHours,
                     peakSeasonHours, overall_sample, country_sample):
    peak_data = pd.DataFrame()
    [country_peak, overall_peak,
     country_hours, overall_hours] = gather_peak_sample(data, seasons,
                                                        regularSeasonHours, 
                                                        peakSeasonHours, 
                                                        country_sample,
                                                        overall_sample)
    for c in country_peak.columns:
        df = pd.DataFrame(
            data={'Node': c, "Period": period, 
                  "Operationalhour": country_hours,
                  "Scenario": "scenario" + str(scenario),
                  "ElectricLoadRaw_in_MW": country_peak[c].values})
        peak_data = pd.concat([peak_data,df], ignore_index=True)
        df = pd.DataFrame(
            data={'Node': c, "Period": period, 
                  "Operationalhour": overall_hours,
                  "Scenario": "scenario" + str(scenario),
                  "ElectricLoadRaw_in_MW": overall_peak[c].values})
        peak_data = pd.concat([peak_data,df], ignore_index=True)
    return peak_data

def sample_generator_peak(data, seasons, g, scenario,
                          period, regularSeasonHours, peakSeasonHours,
                          overall_sample, country_sample):
    peak_data = pd.DataFrame()
    [country_peak, overall_peak,
     country_hours, overall_hours] = gather_peak_sample(data, seasons,
                                                        regularSeasonHours,
                                                        peakSeasonHours, 
                                                        country_sample, 
                                                        overall_sample)
    if g=='Windoffshoregrounded' or g=='Windoffshorefloating':
        startNOnode = 2
    else:
        startNOnode = 1
    for c in country_peak.columns:
        if c == "NO":
            for i in range(startNOnode, 6):
                c_no = c + str(i)
                df = pd.DataFrame(
                data={'Node': c_no, "IntermitentGenerators": g,
                      "Operationalhour": country_hours,
                      "Scenario": "scenario" + str(scenario),
                      "Period": period, 
                      "GeneratorStochasticAvailabilityRaw": 
                          country_peak[c].values})
                peak_data = pd.concat([peak_data,df], ignore_index=True)
                df = pd.DataFrame(
                data={'Node': c_no, "IntermitentGenerators": g, 
                      "Operationalhour": overall_hours, 
                      "Scenario": "scenario" + str(scenario),
                      "Period": period, 
                      "GeneratorStochasticAvailabilityRaw": 
                          overall_peak[c].values})
                peak_data = pd.concat([peak_data,df], ignore_index=True)
        else:
            df = pd.DataFrame(
            data={'Node': c, "IntermitentGenerators": g, 
                  "Operationalhour": country_hours, 
                  "Scenario": "scenario" + str(scenario),
                  "Period": period,
                  "GeneratorStochasticAvailabilityRaw": 
                      country_peak[c].values})
            peak_data = pd.concat([peak_data,df], ignore_index=True)
            df = pd.DataFrame(
            data={'Node': c, "IntermitentGenerators": g, 
                  "Operationalhour": overall_hours,
                  "Scenario": "scenario" + str(scenario),
                  "Period": period,
                 "GeneratorStochasticAvailabilityRaw": 
                     overall_peak[c].values})
            peak_data = pd.concat([peak_data,df], ignore_index=True)
    return peak_data

def generate_random_scenario(filepath, tab_file_path, scenarios, seasons,
                             Periods, regularSeasonHours, peakSeasonHours, 
                             dict_countries,HEATMODULE=False,
                             fix_sample=False):
    
    if fix_sample:
        print("Generating scenarios according to key...")
    else:
        print("Generating random scenarios...")

    # Generate dataframes to print as stochastic-files
    genAvail = pd.DataFrame()
    elecLoad = pd.DataFrame()
    hydroSeasonal = pd.DataFrame()

    if HEATMODULE:
        heatLoad = pd.DataFrame()
        cop = pd.DataFrame()
    
    # Load all the raw scenario data
    solar_data = pd.read_csv(filepath + "/solar.csv")
    windonshore_data = pd.read_csv(filepath + "/windonshore.csv")
    windoffshore_data = pd.read_csv(filepath + "/windoffshore.csv")
    hydrorunoftheriver_data = pd.read_csv(filepath + "/hydroror.csv")
    hydroseasonal_data = pd.read_csv(filepath + "/hydroseasonal.csv")
    electricload_data = pd.read_csv(filepath + "/electricload.csv")

    if HEATMODULE:
        heatload_data = pd.read_csv(filepath + "/HeatModule/heatload.csv")
        cop_data = pd.read_csv(filepath + "/HeatModule/cop_ashp.csv")

    solar_data = make_datetime(solar_data, "%d/%m/%Y %H:%M")
    windonshore_data = make_datetime(windonshore_data, "%d/%m/%Y %H:%M")
    windoffshore_data = make_datetime(windoffshore_data, "%d/%m/%Y %H:%M")
    hydroror_data = make_datetime(hydrorunoftheriver_data, "%Y-%m-%d %H:%M")
    hydroseasonal_data = make_datetime(hydroseasonal_data, "%Y-%m-%d %H:%M")
    electricload_data = make_datetime(electricload_data, "%d/%m/%Y %H:%M")

    if HEATMODULE:
        heatload_data = make_datetime(heatload_data, "%Y-%m-%d %H:%M")
        cop_data = make_datetime(cop_data, "%Y-%m-%d %H:%M")

    if fix_sample:
        sampling_key = pd.read_csv(filepath + "/sampling_key.csv")
        sampling_key = sampling_key.set_index(['Period','Scenario','Season'])
    else:
        sampling_key = pd.DataFrame(columns=['Period','Scenario','Season','Year','Month','Hour'])

    for i in range(1,Periods+1):
        for scenario in range(1,scenarios+1):
            for s in seasons:
                ###################
                ##REGULAR SEASONS##
                ###################

                if fix_sample:
                    sample_year = sampling_key.loc[(i,scenario,s),'Year']
                    sample_month = sampling_key.loc[(i,scenario,s),'Month']
                else:
                     # Get sample year (2015-2019) and month for each season/scenario
                    sample_year = np.random.choice(list(range(2015,2020)))
                    sample_month = np.random.choice(season_month(s))

                # Filter out the hours within the sample year

                solar_month = year_month_filter(solar_data,
                                                        sample_year,
                                                        sample_month)
                windonshore_month = year_month_filter(windonshore_data,
                                                      sample_year,
                                                      sample_month)
                windoffshore_month = year_month_filter(windoffshore_data,
                                                       sample_year,
                                                       sample_month)
                hydroror_month = year_month_filter(hydroror_data,
                                                   sample_year,
                                                   sample_month)
                hydroseasonal_month = year_month_filter(hydroseasonal_data,
                                                        sample_year,
                                                        sample_month)
                electricload_month = year_month_filter(electricload_data,
                                                       sample_year,
                                                       sample_month)

                if HEATMODULE:
                    heatload_month = year_month_filter(heatload_data,
                                                      sample_year,
                                                      sample_month)
                    cop_month = year_month_filter(cop_data,
                                                  sample_year,
                                                  sample_month)
                if fix_sample:
                    sample_hour = sampling_key.loc[(i,scenario,s),'Hour']
                else:
                    sample_hour = np.random.randint(0, solar_month.shape[0] - regularSeasonHours - 1)
                    sampling_key = pd.concat([sampling_key, pd.Series({'Period': i,
                                                        'Scenario': scenario,
                                                        'Season': s,
                                                        'Year': sample_year,
                                                        'Month': sample_month,
                                                        'Hour': sample_hour}).to_frame().T],ignore_index=True)

                    # Sample generator availability for regular seasons
                genAvail = pd.concat([genAvail,
                                  sample_generator(data=solar_month,
                                 regularSeasonHours=regularSeasonHours,
                                 scenario=scenario, season=s,
                                 seasons=seasons, period=i,
                                 generator="Solar",
                                 sample_hour=sample_hour)],ignore_index=True)
                genAvail = pd.concat([genAvail,
                                  sample_generator(data=windonshore_month,
                                 regularSeasonHours=regularSeasonHours,
                                 scenario=scenario, season=s,
                                 seasons=seasons, period=i,
                                 generator="Windonshore",
                                 sample_hour=sample_hour)],ignore_index=True)
                genAvail = pd.concat([genAvail,
                                  sample_generator(data=windoffshore_month,
                                 regularSeasonHours=regularSeasonHours,
                                 scenario=scenario, season=s,
                                 seasons=seasons, period=i,
                                 generator="Windoffshoregrounded",
                                 sample_hour=sample_hour)],ignore_index=True)
                genAvail = pd.concat([genAvail,
                    sample_generator(data=windoffshore_month,
                                     regularSeasonHours=regularSeasonHours,
                                     scenario=scenario, season=s,
                                     seasons=seasons, period=i,
                                     generator="Windoffshorefloating",
                                     sample_hour=sample_hour)],ignore_index=True)
                genAvail = pd.concat([genAvail,
                                      sample_generator(data=hydroror_month,
                                     regularSeasonHours=regularSeasonHours,
                                     scenario=scenario, season=s,
                                     seasons=seasons, period=i,
                                     generator="Hydrorun-of-the-river",
                                     sample_hour=sample_hour)],ignore_index=True)

                # Sample electric load for regular seasons
                elecLoad = pd.concat([elecLoad,
                sample_load(data=electricload_month,
                            regularSeasonHours=regularSeasonHours,
                            scenario=scenario, season=s,
                            seasons=seasons, period=i,
                            sample_hour=sample_hour)],ignore_index=True)

                # Sample seasonal hydro limit for regular seasons
                hydroSeasonal = pd.concat([hydroSeasonal,
                                       sample_hydro(data=hydroseasonal_month,
                             regularSeasonHours=regularSeasonHours,
                             scenario=scenario, season=s,
                             seasons=seasons, period=i,
                             sample_hour=sample_hour)],ignore_index=True)

                # Sample HEATMODULE profiles
                if HEATMODULE:
                    heatLoad = pd.concat([heatLoad,
                        sample_load(data=heatload_month,
                                    regularSeasonHours=regularSeasonHours,
                                    scenario=scenario, season=s,
                                    seasons=seasons, period=i,
                                    sample_hour=sample_hour)],ignore_index=True)

                    cop = pd.concat([cop,
                        sample_generator(data=cop_month,
                                        regularSeasonHours=regularSeasonHours,
                                        scenario=scenario, season=s,
                                        seasons=seasons, period=i,
                                        generator="HeatPumpAir",
                                        sample_hour=sample_hour)],ignore_index=True)
            
            ################
            ##PEAK SEASONS##
            ################

            # Get peak sample year (2015-2019)
            sample_year = np.random.choice(list(range(2015,2020)))

            if fix_sample:
                sample_year = sampling_key.loc[(i,scenario,'peak'),'Year']
            else:
                sampling_key = pd.concat([sampling_key,pd.Series({'Period': i,
                                                    'Scenario': scenario,
                                                    'Season': 'peak',
                                                    'Year': sample_year,
                                                    'Month': 0,
                                                    'Hour': 0}).to_frame().T],
                                                    ignore_index=True)

            solar_data_year = solar_data.loc[solar_data.year.isin([sample_year]), :]
            windonshore_data_year = windonshore_data.loc[windonshore_data.year.isin([sample_year]), :]
            windoffshore_data_year = windoffshore_data.loc[windoffshore_data.year.isin([sample_year]), :]
            hydroror_data_year = hydroror_data.loc[hydroror_data.year.isin([sample_year]), :]
            hydroseasonal_data_year = hydroseasonal_data.loc[hydroseasonal_data.year.isin([sample_year]), :]
            electricload_data_year = electricload_data.loc[electricload_data.year.isin([sample_year]), :]

            if HEATMODULE:
                heatload_year = heatload_data.loc[heatload_data.year.isin([sample_year])]
                cop_year = cop_data.loc[cop_data.year.isin([sample_year])]
            
            #Peak1: The highest load when all loads are summed together
            electricload_data_year_notime = remove_time_index(electricload_data_year)
            overall_sample = electricload_data_year_notime.sum(axis=1).idxmax()
            #Peak2: The highest load of a single country
            max_load_country = electricload_data_year_notime.max().idxmax()
            country_sample = electricload_data_year_notime[max_load_country].idxmax()

            #Sample generator availability for peak seasons
            genAvail = pd.concat([genAvail,
                sample_generator_peak(data=solar_data_year,
                                      seasons=seasons,
                                      g="Solar", scenario=scenario, period=i,
                                      regularSeasonHours=regularSeasonHours,
                                      peakSeasonHours=peakSeasonHours,
                                      overall_sample=overall_sample,
                                      country_sample=country_sample)],ignore_index=True)
            genAvail = pd.concat([genAvail,
                sample_generator_peak(data=windonshore_data_year,
                                      seasons=seasons, 
                                      g="Windonshore", scenario=scenario, 
                                      period=i, 
                                      regularSeasonHours=regularSeasonHours,
                                      peakSeasonHours=peakSeasonHours,
                                      overall_sample=overall_sample, 
                                      country_sample=country_sample)],ignore_index=True)
            genAvail = pd.concat([genAvail,
                sample_generator_peak(data=windoffshore_data_year,
                                      seasons=seasons, 
                                      g="Windoffshoregrounded", scenario=scenario,
                                      period=i, 
                                      regularSeasonHours=regularSeasonHours, 
                                      peakSeasonHours=peakSeasonHours, 
                                      overall_sample=overall_sample, 
                                      country_sample=country_sample)],ignore_index=True)
            genAvail = pd.concat([genAvail,
                sample_generator_peak(data=windoffshore_data_year,
                                      seasons=seasons, 
                                      g="Windoffshorefloating", scenario=scenario,
                                      period=i, 
                                      regularSeasonHours=regularSeasonHours, 
                                      peakSeasonHours=peakSeasonHours, 
                                      overall_sample=overall_sample, 
                                      country_sample=country_sample)],ignore_index=True)
            genAvail = pd.concat([genAvail,
                sample_generator_peak(data=hydroror_data_year,
                                      seasons=seasons, 
                                      g="Hydrorun-of-the-river",
                                      scenario=scenario, period=i, 
                                      regularSeasonHours=regularSeasonHours,
                                      peakSeasonHours=peakSeasonHours,
                                      overall_sample=overall_sample, 
                                      country_sample=country_sample)],ignore_index=True)
            
            #Sample electric load for peak seasons
            elecLoad = pd.concat([elecLoad,
                sample_load_peak(data=electricload_data_year,
                                 seasons=seasons,
                                 scenario=scenario, period=i, 
                                 regularSeasonHours=regularSeasonHours, 
                                 peakSeasonHours=peakSeasonHours,
                                 overall_sample=overall_sample, 
                                 country_sample=country_sample)],ignore_index=True)
            
            #Sample seasonal hydro limit for peak seasons
            hydroSeasonal = pd.concat([hydroSeasonal,
                sample_hydro_peak(data=hydroseasonal_data_year,
                                  seasons=seasons,
                                  scenario=scenario, period=i, 
                                  regularSeasonHours=regularSeasonHours, 
                                  peakSeasonHours=peakSeasonHours,
                                  overall_sample=overall_sample, 
                                  country_sample=country_sample)],ignore_index=True)

            # Sample HEATMODULE profiles
            if HEATMODULE:
                heatLoad = pd.concat([heatLoad,
                    sample_load_peak(data=heatload_year,
                                     seasons=seasons,
                                     scenario=scenario, period=i,
                                     regularSeasonHours=regularSeasonHours,
                                     peakSeasonHours=peakSeasonHours,
                                     overall_sample=overall_sample,
                                     country_sample=country_sample)],ignore_index=True)

                cop = pd.concat([cop,
                    sample_generator_peak(data=cop_year,
                                          seasons=seasons,
                                          g="HeatPumpAir",
                                          scenario=scenario, period=i,
                                          regularSeasonHours=regularSeasonHours,
                                          peakSeasonHours=peakSeasonHours,
                                          overall_sample=overall_sample,
                                          country_sample=country_sample)],ignore_index=True)

    #Replace country codes with country names
    genAvail = genAvail.replace({"Node": dict_countries})
    elecLoad = elecLoad.replace({"Node": dict_countries})
    hydroSeasonal = hydroSeasonal.replace({"Node": dict_countries})

    if HEATMODULE:
        heatLoad = heatLoad.replace({"Node": dict_countries})
        cop = cop.replace({"Node": dict_countries})

    #Make header for .tab-file
    genAvail = genAvail[["Node", "IntermitentGenerators", "Operationalhour",
                         "Scenario", "Period",
                         "GeneratorStochasticAvailabilityRaw"]]
    elecLoad = elecLoad[["Node", "Operationalhour", "Scenario","Period", 
                         'ElectricLoadRaw_in_MW']]
    hydroSeasonal = hydroSeasonal[["Node", "Period", "Season", 
                                   "Operationalhour", "Scenario",
                                   "HydroGeneratorMaxSeasonalProduction"]]

    if HEATMODULE:
        heatLoad = heatLoad[["Node", "Operationalhour", "Scenario","Period",
                             'ElectricLoadRaw_in_MW']]
        cop = cop[["Node", "IntermitentGenerators", "Operationalhour",
                   "Scenario", "Period", "GeneratorStochasticAvailabilityRaw"]]

    #Make filepath (if it does not exist) and print .tab-files
    if not os.path.exists(tab_file_path):
        os.makedirs(tab_file_path)

    # Save sampling key
    if fix_sample:
        sampling_key = sampling_key.reset_index(level=['Period','Scenario','Season'])

    sampling_key.to_csv(
        tab_file_path + "/sampling_key" + '.csv',
        header=True, index=None, mode='w')

    genAvail.to_csv(
        tab_file_path + "/Stochastic_StochasticAvailability" + '.tab',
        header=True, index=None, sep='\t', mode='w')
    elecLoad.to_csv(
        tab_file_path + "/Stochastic_ElectricLoadRaw" + '.tab',
        header=True, index=None, sep='\t', mode='w')
    hydroSeasonal.to_csv(
        tab_file_path + "/Stochastic_HydroGenMaxSeasonalProduction" + '.tab',
        header=True, index=None, sep='\t', mode='w')

    if HEATMODULE:
        if not os.path.exists(tab_file_path + "/HeatModule"):
            os.makedirs(tab_file_path + "/HeatModule")
        heatLoad.to_csv(
            tab_file_path + "/HeatModule/HeatModuleStochastic_HeatLoadRaw.tab",
            header=True, index=None, sep='\t', mode='w')
        cop.to_csv(
            tab_file_path + "/HeatModule/HeatModuleStochastic_ConverterAvail.tab",
            header=True, index=None, sep='\t', mode='w')