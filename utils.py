import math
import discord
import asyncio
import json
from datetime import datetime
from typing import Union
import aiohttp
from lxml import html
import re
from main import mongo

def embed_pager(title: str, fields: list, description: str = "", color: int = 0x00ff00, inline: bool = True) -> list:
    embeds = []
    for i in range(math.ceil(len(fields)/24)):
        embeds.append(discord.Embed(title=f"{title} page {i+1}", description=description, color=color)) 
    index = 0
    n = 0
    for field in fields:
        embeds[index].add_field(name=f"{field['name']}", value=field['value'], inline=inline)
        n += 1
        if n % 24 == 0:
            index += 1
    return embeds
                
async def reaction_checker(self, message: discord.Message, embeds: list) -> None:
    reactions = []
    for i in range(len(embeds)):
        reactions.append(asyncio.create_task(message.add_reaction(f"{i+1}\N{variation selector-16}\N{combining enclosing keycap}")))
    await asyncio.gather(*reactions)
    while True:
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=600)
            if user.bot == True or reaction.message != message:
                continue

            elif "\N{variation selector-16}\N{combining enclosing keycap}" in str(reaction.emoji):
                await message.edit(embed=embeds[int(str(reaction.emoji)[0])-1])
                await message.remove_reaction(reaction, user)

        except asyncio.TimeoutError:
            await message.edit(content="**Command timed out!**")
            break

async def find_user(self, arg: Union[str, int]) -> dict:
    current = current = list(mongo['users'].find({}))
    members = self.bot.get_all_members()
    guild = self.bot.get_guild(434071714893398016)
    heathen_role = guild.get_role(434248817005690880)
    try:
        await self.bot.fetch_user(int(arg))
        for x in current:
            if x['user'] == int(arg):
                return x
    except:
        try:
            arg.startswith('<@') and arg.endswith('>')
            if arg.startswith('<@!'):
                user_id = arg[(arg.index('!')+1):arg.index('>')]
            else:
                user_id = arg[(arg.index('@')+1):arg.index('>')]
            for x in current:
                if x['user'] == int(user_id):
                    return x
        except:
            try:
                int(arg)
                for x in current:
                    if x['nationid'] == arg:
                        return x
            except:
                try:
                    for member in members:
                        if arg.lower() in member.name.lower() and heathen_role not in member.roles:
                            x = mongo.users.find_one({"user": member.id})
                            return x
                        elif arg.lower() in member.display_name.lower() and heathen_role not in member.roles:
                            x = mongo.users.find_one({"user": member.id})
                            return x
                        elif str(member).lower() == arg.lower() and heathen_role not in member.roles:
                            x = mongo.users.find_one({"user": member.id})
                            return x
                        for x in current:
                            if arg.lower() in x['name'].lower():
                                return x
                            elif arg.lower() in x['leader'].lower():
                                return x
                    raise
                except:
                    try:
                        for x in current:
                            if x['nationid'] == arg[(arg.index('=')+1):]:
                                return x
                    finally:
                        pass
                finally:
                    pass
            finally:
                pass
        finally:
            pass
    finally:
        return {}

async def find_nation(arg: Union[str, int]) -> Union[dict, None]:
    try:
        result = list(mongo.world_nations.find({"nation": arg}).collation(
            {"locale": "en", "strength": 1}))[0]
    except:
        try:
            result = list(mongo.world_nations.find({"leader": arg}).collation(
                {"locale": "en", "strength": 1}))[0]
        except:
            try:
                arg = int(re.sub("[^0-9]", "", arg))
                result = list(mongo.world_nations.find({"nationid": arg}).collation(
                    {"locale": "en", "strength": 1}))[0]
            except:
                result = None
    return result

async def find_nation_plus(self, arg: Union[str, int]) -> Union[dict, None]: # only returns a nation if it is at least 1 day old
    nation = await self.find_nation(arg)
    if nation == None:
        nation = await self.find_user(arg)
        if nation == {}:
            return None
        else:
            nation = await self.find_nation(nation['nationid'])
            if nation == None:
                return None
    return nation

async def pre_revenue_calc(mongo, cipher_suite, api_key, message: discord.Message, query_for_nation: bool = False, nationid: Union[int, str] = None, parsed_nation: dict = None):
    async with aiohttp.ClientSession() as session:
        if query_for_nation:
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{nationid}){{data{{nation_name leader_name id continent color dompolicy alliance_id alliance{{name id}} num_cities soldiers tanks aircraft ships missiles nukes offensive_wars{{date turnsleft attid winner att_gas_used att_mun_used att_steel_used att_alum_used def_infra_destroyed_value def_gas_used def_mun_used def_steel_used def_alum_used att_infra_destroyed_value attacks{{loot_info victor moneystolen}}}} defensive_wars{{date turnsleft attid winner att_gas_used att_mun_used att_steel_used att_alum_used def_infra_destroyed_value def_gas_used def_mun_used def_steel_used def_alum_used att_infra_destroyed_value attacks{{loot_info victor moneystolen}}}} ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap cities{{id date powered infrastructure land oilpower windpower coalpower nuclearpower coalmine oilwell uramine barracks farm policestation hospital recyclingcenter subway supermarket bank mall stadium leadmine ironmine bauxitemine gasrefinery aluminumrefinery steelmill munitionsfactory factory airforcebase drydock}}}}}}}}"}) as temp:
                nation = (await temp.json())['data']['nations']['data']
            if len(nation) == 0:
                print("That person was not in the API!")
                raise 
            else:
                nation = nation[0]
        else:
            nation = parsed_nation

        await message.edit(content="Getting color bloc values...")
        async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{colors{{color turn_bonus}}}}"}) as temp:
            res_colors = (await temp.json())['data']['colors']
        colors = {}
        for color in res_colors:
            colors[color['color']] = color['turn_bonus'] * 12

        await message.edit(content="Getting resource prices...")
        async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{tradeprices(limit:1){{coal oil uranium iron bauxite lead gasoline munitions steel aluminum food}}}}"}) as temp:
            prices = (await temp.json())['data']['tradeprices'][0]
        prices['money'] = 1

        await message.edit(content="Getting treasures...")
        async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{treasures{{bonus nation{{id alliance_id}}}}}}"}) as temp:
            treasures = (await temp.json())['data']['treasures']

        await message.edit(content="Getting food modifiers...")
        banker = mongo.users.find_one({"user": 465463547200012298})
        login_url = "https://politicsandwar.com/login/"
        login_data = {
            "email": str(cipher_suite.decrypt(banker['email'].encode()))[2:-1],
            "password": str(cipher_suite.decrypt(banker['pwd'].encode()))[2:-1],
            "loginform": "Login"
        }
        await session.post(login_url, data=login_data)

        radiation_page = await session.get(f"https://politicsandwar.com/world/radiation/")
        tree = html.fromstring(await radiation_page.text())
        info = tree.xpath("//div[@class='col-md-10']/div[@class='row']/div/p")
        for x in info.copy():
            #print(x.text_content())
            if "Food" not in x.text_content():
                info.remove(x)
            else:
                info.remove(x)
                x = re.sub(r"[^0-9.]+", "", x.text_content().strip())
                info.append(x)
        radiation = {"na": 1 - float(info[0])/100, "sa": 1 - float(info[1])/100, "eu": 1 - float(info[2])/100, "as": 1 - float(info[3])/100, "af": 1 - float(info[4])/100, "au": 1 - float(info[5])/100, "an": 1 - float(info[6])/100}

        info2 = tree.xpath("//div[@class='sidebar'][contains(@style,'padding-left: 20px;')]/text()")
        date = info2[2].strip()
        seasonal_mod = {"na": 1, "sa": 1, "eu": 1, "as": 1, "af": 1, "au": 1, "an": 0.5}
        if "June" in date or "July" in date or "August" in date:
            seasonal_mod['na'] = 1.2
            seasonal_mod['as'] = 1.2
            seasonal_mod['eu'] = 1.2
            seasonal_mod['sa'] = 0.8
            seasonal_mod['af'] = 0.8
            seasonal_mod['au'] = 0.8
        elif "December" in date or "January" in date or "February" in date:
            seasonal_mod['na'] = 0.8
            seasonal_mod['as'] = 0.8
            seasonal_mod['eu'] = 0.8
            seasonal_mod['sa'] = 1.2
            seasonal_mod['af'] = 1.2
            seasonal_mod['au'] = 1.2

        return nation, colors, prices, treasures, radiation, seasonal_mod

async def revenue_calc(message: discord.Message, nation: dict, radiation: dict, treasures: dict, prices: dict, colors: dict, seasonal_mod: dict, build: str = None, single_city: bool = False) -> dict:
    max_commerce = 100
    base_com = 0
    hos_dis_red = 2.5
    alu_mod = 1
    mun_mod = 1
    gas_mod = 1
    manu_poll_mod = 1
    farm_poll_mod = 0.5
    subw_poll_red = 45
    rss_upkeep_mod = 1
    ste_mod = 1
    rec_poll = 70
    pol_cri_red = 2.5
    food_land_mod = 500
    uranium_mod = 1
    rss_upkeep = 0
    civil_upkeep = 0
    military_upkeep = 0
    money_income = 0
    power_upkeep = 0
    nationpop = 0 
    color_bonus = 0
    policy_bonus = 1
    new_player_bonus = 1
    mil_cost = 1
    total_infra = 0
    starve_net_text = ""
    starve_money_text = ""
    starve_exp_text = ""
    color_text = ""
    new_player_text = ""
    policy_bonus_text = ""
    treasure_text = ""
    footer = ""
    
    if nation['ironw'] == True:
        ste_mod = 1.36
    if nation['bauxitew'] == True:
        alu_mod = 1.36
    if nation['armss'] == True:
        mun_mod = 1.34
    if nation['egr'] == True:
        gas_mod = 2
    if nation['massirr'] == True:
        food_land_mod = 400
    if nation['itc'] == True:
        max_commerce = 115
    if nation['telecom_satellite'] == True:
        max_commerce = 125
        base_com = 2
    if nation['recycling_initiative'] == True:
        rec_poll = 75
    if nation['green_tech'] == True:
        manu_poll_mod = 0.75
        farm_poll_mod = 0.5
        subw_poll_red = 70
        rss_upkeep_mod = 0.9
    if nation['clinical_research_center'] == True:
        hos_dis_red = 3.5
    if nation['specialized_police_training'] == True:
        hos_dis_red = 3.5
    if nation['uap'] == True:
        uranium_mod = 2

    coal = 0
    oil = 0
    uranium = 0
    lead = 0
    iron = 0
    bauxite = 0
    gasoline = 0
    munitions = 0
    steel = 0
    aluminum = 0
    food = 0

    if build != None:
        try:
            build = json.loads(build)
        except json.JSONDecodeError:
            await message.edit(content="Something is wrong with the build you sent!")
            return
        land = 0
        for city in nation['cities']:
            land += city['land']
        city = {}
        for key, value in build.items():
            city[key[4:]] = int(value)
        city['infrastructure'] = city.pop('a_needed')
        city['land'] = round(land/nation['num_cities'])
        city['powered'] = True
        city['date'] = nation['cities'][math.ceil(nation['num_cities']/2)]['date']
        nation['cities'] = [city]
        #print(city)

    for city in nation['cities']:
        total_infra += city['infrastructure']
        base_pop = city['infrastructure'] * 100
        pollution = 0
        unpowered_infra = city['infrastructure']
        for wind_plant in range(city['windpower']): #can add something about wasted slots
            if unpowered_infra > 0:
                unpowered_infra -= 250
                power_upkeep += 42
        for nucl_plant in range(city['nuclearpower']): 
            power_upkeep += 10500
            for level in range(2):
                if unpowered_infra > 0:
                    unpowered_infra -= 1000
                    uranium -= 1.2
        for oil_plant in range(city['oilpower']): 
            power_upkeep += 1800 
            pollution += 6
            for level in range(5):
                if unpowered_infra > 0:
                    unpowered_infra -= 100
                    oil -= 1.2
        for coal_plant in range(city['coalpower']): 
            power_upkeep += 1200  
            pollution += 8
            for level in range(5):
                if unpowered_infra > 0:
                    unpowered_infra -= 100
                    coal -= 1.2

        rss_upkeep += 400 * city['coalmine'] * rss_upkeep_mod
        pollution += 12 * city['coalmine']
        coal += 3 * city['coalmine'] * (1 + ((0.5 * (city['coalmine'] - 1)) / (10 - 1)))

        rss_upkeep += 600 * city['oilwell'] * rss_upkeep_mod
        pollution += 12 * city['oilwell']
        oil += 3 * city['oilwell'] * (1 + ((0.5 * (city['oilwell'] - 1)) / (10 - 1)))

        rss_upkeep += 5000 * city['uramine'] * rss_upkeep_mod
        pollution += 20 * city['uramine']
        uranium += 3 * city['uramine'] * (1 + ((0.5 * (city['uramine'] - 1)) / (5 - 1))) * uranium_mod

        rss_upkeep += 1500 * city['leadmine'] * rss_upkeep_mod
        pollution += 12 * city['leadmine']
        lead += 3 * city['leadmine'] * (1 + ((0.5 * (city['leadmine'] - 1)) / (10 - 1)))

        rss_upkeep += 1600 * city['ironmine'] * rss_upkeep_mod
        pollution += 12 * city['ironmine']
        iron += 3 * city['ironmine'] * (1 + ((0.5 * (city['ironmine'] - 1)) / (10 - 1)))

        rss_upkeep += 1600 * city['bauxitemine'] * rss_upkeep_mod
        pollution += 12 * city['bauxitemine']
        bauxite += 3 * city['bauxitemine'] * (1 + ((0.5 * (city['bauxitemine'] - 1)) / (10 - 1)))

        rss_upkeep += 300 * city['farm'] * rss_upkeep_mod ## seasonal modifiers and radiation
        pollution += 2 * city['farm'] * farm_poll_mod
        food_prod = city['land']/food_land_mod * city['farm'] * (1 + ((0.5 * (city['farm'] - 1)) / (20 - 1))) * seasonal_mod[nation['continent']] * radiation[nation['continent']] * 12
        if food_prod < 0:
            food += 0
        else:
            food += food_prod
        
        commerce = base_com
        if city['powered']:
            rss_upkeep += 4000 * city['gasrefinery'] * rss_upkeep_mod
            pollution += 32 * city['gasrefinery'] * manu_poll_mod
            oil -= 3 * city['gasrefinery'] * (1 + ((0.5 * (city['gasrefinery'] - 1)) / (5 - 1))) * gas_mod
            gasoline += 6 * city['gasrefinery'] * (1 + ((0.5 * (city['gasrefinery'] - 1)) / (5 - 1))) * gas_mod

            rss_upkeep += 4000 * city['steelmill'] * rss_upkeep_mod
            pollution += 40 * city['steelmill'] * manu_poll_mod
            iron -= 3 * city['steelmill'] * (1 + ((0.5 * (city['steelmill'] - 1)) / (5 - 1))) * ste_mod
            coal -= 3 * city['steelmill'] * (1 + ((0.5 * (city['steelmill'] - 1)) / (5 - 1))) * ste_mod
            steel += 9 * city['steelmill'] * (1 + ((0.5 * (city['steelmill'] - 1)) / (5 - 1))) * ste_mod

            rss_upkeep += 2500 * city['aluminumrefinery'] * rss_upkeep_mod
            pollution += 40 * city['aluminumrefinery'] * manu_poll_mod
            bauxite -= 3 * city['aluminumrefinery'] * (1 + ((0.5 * (city['aluminumrefinery'] - 1)) / (5 - 1))) * alu_mod
            aluminum += 9 * city['aluminumrefinery'] * (1 + ((0.5 * (city['aluminumrefinery'] - 1)) / (5 - 1))) * alu_mod

            rss_upkeep += 3500 * city['munitionsfactory'] * rss_upkeep_mod
            pollution += 32 * city['munitionsfactory'] * manu_poll_mod
            lead -= 6 * city['munitionsfactory'] * (1 + ((0.5 * (city['munitionsfactory'] - 1)) / (5 - 1))) * mun_mod
            munitions += 18 * city['munitionsfactory'] * (1 + ((0.5 * (city['munitionsfactory'] - 1)) / (5 - 1))) * mun_mod
                
            civil_upkeep += city['policestation'] * 750 
            civil_upkeep += city['hospital'] * 1000 
            civil_upkeep += city['recyclingcenter'] * 2500 
            civil_upkeep += city['subway'] * 3250 
            civil_upkeep += city['supermarket'] * 600 
            civil_upkeep += city['bank'] * 1800 
            civil_upkeep += city['mall'] * 5400
            civil_upkeep += city['stadium'] * 12150 

            police_stations = city['policestation']
            hospitals = city['hospital']

            pollution += city['policestation']
            pollution += city['hospital'] * 4
            pollution -= city['recyclingcenter'] * rec_poll
            pollution -= city['subway'] * subw_poll_red
            pollution += city['mall'] * 2
            pollution += city['stadium'] * 5

            city['real_pollution'] = pollution
            if pollution < 0:
                pollution = 0
            city['pollution'] = pollution

            commerce += city['subway'] * 8
            commerce += city['supermarket'] * 3 
            commerce += city['bank'] * 5 
            commerce += city['mall'] * 9
            commerce += city['stadium'] * 12 

            city['real_commerce'] = commerce
            if commerce > max_commerce:
                commerce = max_commerce
            city['commerce'] = commerce

        else:
            police_stations = 0
            hospitals = 0

        crime_rate = ((103 - commerce)**2 + (city['infrastructure'] * 100))/(111111) - police_stations * pol_cri_red
        city['real_crime_rate'] = crime_rate
        if crime_rate < 0:
            crime_rate = 0
        city['crime_rate'] = crime_rate
        crime_deaths = ((crime_rate) / 10) * (100 * city['infrastructure']) - 25
        disease_rate = (((((base_pop / city['land'])**2) * 0.01) - 25)/100) + (base_pop/100000) + pollution * 0.05 - hospitals * hos_dis_red
        city['real_disease_rate'] = disease_rate
        if disease_rate > 100:
            disease_rate = 100
        elif disease_rate < 0:
            disease_rate = 0
        city['disease_rate'] = disease_rate
        disease_deaths = base_pop * (disease_rate/100)
        if disease_deaths < 0:
            disease_deaths = 0
        city_age = (datetime.utcnow() - datetime.strptime(city['date'], "%Y-%m-%d")).days
        if city_age == 0:
            city_age = 1
        population = ((base_pop - disease_deaths - crime_deaths) * (1 + math.log(city_age)/15))
        nationpop += population
        money_income += (((commerce / 50) * 0.725) + 0.725) * population
    
    alliance_treasures = 0
    nation_treasure_bonus = 1
    for treasure in treasures:
        if treasure['nation'] == None:
            continue
        if treasure['nation']['id'] == nation['id']:
            nation_treasure_bonus += treasure['bonus'] / 100
        if nation['alliance']:
            if treasure['nation']['alliance_id'] == nation['alliance_id']:
                alliance_treasures += 1
    if alliance_treasures > 0:
        nation_treasure_bonus += math.sqrt(alliance_treasures * 4) / 100
    if nation_treasure_bonus > 1:
        treasure_text = f"\n\nTreasure Bonus: ${round(money_income * (nation_treasure_bonus - 1)):,}"
    
    if not single_city:
        color_bonus = colors[nation['color']]
        color_text = f"\n\nColor Trade Bloc Bonus: ${round(color_bonus):,}"
    food -= nationpop / 1000

    if nation['num_cities'] < 11:
        new_player_bonus = 2.1 - 0.1 * nation['num_cities']
        new_player_text = f"\n\nNew Player Bonus: ${round((new_player_bonus - 1) * money_income):,}"
    if nation['dompolicy'] == "Open Markets":
        policy_bonus = 1.01
        policy_bonus_text = f"\n\nOpen Markets Bonus: ${round(money_income * 0.01):,}"
    
    at_war = False
    if not single_city:
        for war in nation['offensive_wars']:
            if war['turnsleft'] > 0:
                at_war = True
        for war in nation['defensive_wars']:
            if war['turnsleft'] > 0:
                at_war = True
        if not at_war:
            military_upkeep += nation['soldiers'] * 1.25
            food -= nation['soldiers'] / 750
            military_upkeep += nation['tanks'] * 50
            military_upkeep += nation['aircraft'] * 500
            military_upkeep += nation['ships'] * 3750
            military_upkeep += nation['missiles'] * 21000
            military_upkeep += nation['nukes'] * 31500 
        else:
            military_upkeep += nation['soldiers'] * 1.88
            food -= nation['soldiers'] / 500
            military_upkeep += nation['tanks'] * 75
            military_upkeep += nation['aircraft'] * 750
            military_upkeep += nation['ships'] * 5625
            military_upkeep += nation['missiles'] * 35000 
            military_upkeep += nation['nukes'] * 52500
    else:
        military_upkeep += int(city['barracks']) * 3000 * 1.25
        military_upkeep += int(city['factory']) * 250 * 50
        military_upkeep += int(city['airforcebase']) * 15 * 500
        military_upkeep += int(city['drydock']) * 5 * 3750

    if nation['dompolicy'] == "Imperialism":
        mil_cost = 0.95
        policy_bonus_text = f"\n\nImperialism Bonus: ${round(military_upkeep * 0.05):,}"
    if food < 0:
        starve_exp_text = f"\n\nPossible Starvation Penalty: ${round(money_income * policy_bonus * new_player_bonus * 0.33):,}*"
        starve_money_text = f" (${round(money_income * policy_bonus * new_player_bonus * 0.67 + color_bonus - power_upkeep - rss_upkeep - military_upkeep * mil_cost - civil_upkeep):,}*)"
        starve_net_text = f" (${round(money_income * policy_bonus * new_player_bonus * 0.67 + color_bonus - power_upkeep - rss_upkeep - military_upkeep * mil_cost - civil_upkeep + coal * prices['coal'] + oil * prices['oil'] + uranium * prices['uranium'] + lead * prices['lead'] + iron * prices['iron'] + bauxite * prices['bauxite'] + gasoline * prices['gasoline'] + munitions * prices['munitions'] + steel * prices['steel'] + aluminum * prices['aluminum'] + food * prices['food']):,}*)"
        footer = "* The income if the nation is suffering from a starvation penalty"
    
    max_infra = sorted(nation['cities'], key=lambda k: k['infrastructure'], reverse=True)[0]['infrastructure']

    if single_city:
        rev_obj = nation['cities'][0]
    else:
        rev_obj = {}
    rev_obj['monetary_net_num'] = round(money_income * policy_bonus * new_player_bonus * nation_treasure_bonus + color_bonus - power_upkeep - rss_upkeep - military_upkeep * mil_cost - civil_upkeep + coal * prices['coal'] + oil * prices['oil'] + uranium * prices['uranium'] + lead * prices['lead'] + iron * prices['iron'] + bauxite * prices['bauxite'] + gasoline * prices['gasoline'] + munitions * prices['munitions'] + steel * prices['steel'] + aluminum * prices['aluminum'] + food * prices['food'])
    rev_obj['net_cash_num'] = round(money_income * policy_bonus * new_player_bonus * nation_treasure_bonus + color_bonus - power_upkeep - rss_upkeep - military_upkeep * mil_cost - civil_upkeep)
    rev_obj['food'] = food
    if single_city:
        rev_obj['money'] = rev_obj['net_cash_num']
        rev_obj['net income'] = rev_obj['monetary_net_num']
        rev_obj['aluminum'] = aluminum
        rev_obj['bauxite'] = bauxite
        rev_obj['coal'] = coal
        rev_obj['gasoline'] = gasoline
        rev_obj['iron'] = iron
        rev_obj['lead'] = lead
        rev_obj['munitions'] = munitions
        rev_obj['oil'] = oil
        rev_obj['steel'] = steel
        rev_obj['uranium'] = uranium
        rev_obj['disease_rate'] = disease_rate
        rev_obj['crime_rate'] = crime_rate
        rev_obj['commerce'] = commerce
        rev_obj['pollution'] = pollution
        return rev_obj
    else:
        rev_obj['nation'] = nation
    rev_obj['footer'] = footer
    rev_obj['max_infra'] = max_infra
    rev_obj['avg_infra'] = round(total_infra / nation['num_cities'])
    rev_obj['income_txt']=f"National Tax Revenue: ${round(money_income):,}{color_text}{new_player_text}{policy_bonus_text}{treasure_text}"
    rev_obj['expenses_txt']=f"Power Plant Upkeep: ${round(power_upkeep):,}\n\nResource Prod. Upkeep: ${round(rss_upkeep):,}\n\nMilitary Upkeep (excl. spies): ${round(military_upkeep * mil_cost):,}\n\nCity Improvement Upkeep: ${round(civil_upkeep):,}{starve_exp_text}"
    rev_obj['net_rev_txt']=f"Coal: {round(coal):,}\nOil: {round(oil):,}\nUranium: {round(uranium):,}\nLead: {round(lead):,}\nIron: {round(iron):,}\nBauxite: {round(bauxite):,}\nGasoline: {round(gasoline):,}\nMunitions: {round(munitions):,}\nSteel: {round(steel):,}\nAluminum: {round(aluminum):,}\nFood: {round(food):,}\nMoney: ${round(money_income * policy_bonus * new_player_bonus * nation_treasure_bonus + color_bonus - power_upkeep - rss_upkeep - military_upkeep * mil_cost - civil_upkeep):,}{starve_money_text}"
    rev_obj['mon_net_txt']=f"${round(money_income * policy_bonus * new_player_bonus * nation_treasure_bonus + color_bonus - power_upkeep - rss_upkeep - military_upkeep * mil_cost - civil_upkeep + coal * prices['coal'] + oil * prices['oil'] + uranium * prices['uranium'] + lead * prices['lead'] + iron * prices['iron'] + bauxite * prices['bauxite'] + gasoline * prices['gasoline'] + munitions * prices['munitions'] + steel * prices['steel'] + aluminum * prices['aluminum'] + food * prices['food']):,}{starve_net_text}"
    rev_obj['money_txt']=f"${round(money_income * policy_bonus * new_player_bonus * nation_treasure_bonus + color_bonus - power_upkeep - rss_upkeep - military_upkeep * mil_cost - civil_upkeep):,}{starve_money_text}"
    return rev_obj