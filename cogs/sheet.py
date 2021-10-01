from mako.template import Template
import aiohttp
import os.path
from main import mongo
from datetime import datetime
from discord.ext import commands
import os
api_key = os.getenv("api_key")
convent_key = os.getenv("convent_api_key")

class Sheet(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def getsheet(self, ctx):
        print('getting sheet')
        await self.sheet_generator()
        await ctx.send('Finito!')

    async def sheet_generator(self):
        async with aiohttp.ClientSession() as session:
            template = """
    <!DOCTYPE html>
    <body>
        <div style="overflow-x:auto;">
            <style>
                table {
                    font-family: Verdana, Arial, Monaco;
                    font-size: 80%;
                    border-collapse: collapse;
                    width: 100%;


                }

                th {
                    text-align: left;
                    padding: 8px;
                }

                tr:nth-child(even) {
                    background-color: #f2f2f2
                }

                th {
                    background-color: #4CAF50;
                    color: white;
                    cursor: pointer;
                }

                th:hover {
                    background-color: #008000;
                }

                td {
                    position: relative;
                    text-align: left;
                    padding: 2px 6px;
                    white-space: nowrap;
                }

                tr.strikeout td:before {
                    content: " ";
                    position: absolute;
                    top: 50%;
                    left: 0;
                    border-bottom: 1px solid #111;
                    width: 100%;
                }

            </style>
            <table id="grid">
                <thead>
                    <tr>
                        <th data-type="number">Nation id</th>
                        <th data-type="string">Nation name</th>
                        <th data-type="string">Leader name</th>
                        <th data-type="string">Discord username</th>
                        <th data-type="number">Discord id</th>
                        <th data-type="string">Color</th>
                        <th data-type="string">Alliance</th>
                        <th data-type="number">Cities</th>
                        <th data-type="number">Infra/city</th>
                        <th data-type="number">Score</th>
                        <th data-type="number">VM</th>
                        <th data-type="number">Hours inactive</th>
                        <th data-type="number">Soldiers milt.</th>
                        <th data-type="number">Tanks milt.</th>
                        <th data-type="number">Aircraft milt.</th>
                        <th data-type="number">Ships milt.</th>
                        <th data-type="number">Total milt.</th>
                        <th data-type="string">Avg. MMR</th>
                        <th data-type="string">Audited</th>
                        % for rs in ['Aluminum', 'Bauxite', 'Coal', 'Food', 'Gasoline', 'Iron', 'Lead', 'Money', 'Munitions', 'Oil', 'Steel', 'Uranium', 'Total bal.']:
                            <th data-type="number">${rs}</th>
                        % endfor
                        
                    </tr>
                </thead>
                <tbody>
                    % for nation in nations:
                        % if int(nation['vmode']) > 0:
                        <tr class="strikeout">
                        % else:
                        <tr>
                        % endif

                        <td>${nation['id']}</td>
                        <td><a href="https://politicsandwar.com/nation/id=${nation['id']}" target="_blank">${nation['nation_name']}</a></td>
                        <td>${nation['leader_name']}</td>
                        <td>${nation['user_object']['username']}</td>
                        <td>${nation['user_object']['discordid']}</td>

                        % if nation['alliance_id'] == "7531" and nation['color'] not in ['beige','blue']:
                        <td style="color:red">${nation['color']}</td>
                        % elif nation['alliance_id'] == "4729" and nation['color'] not in ['beige','green']:
                        <td style="color:red">${nation['color']}</td>
                        % else:
                        <td>${nation['color']}</td>
                        % endif
                        
                        % if nation['num_cities'] >= 15 and nation['alliance_id'] == "7531":
                        <td style="color:red">Convent of Atom</td>
                        % elif nation['alliance_id'] == "7531":
                        <td>Convent of Atom</td>
                        % elif nation['alliance_id'] == "4729":
                        <td>Church of Atom</td>
                        % else:
                        <td>¯\_(ツ)_/¯</td>
                        % endif

                        <td>${nation['num_cities']}</td>

                        % if round(float(nation['infrastructure'])/nation['num_cities'],2) > 2500:
                        <td style="color:red">${round(float(nation['infrastructure'])/nation['num_cities'],2)}</td>
                        % else: 
                        <td>${round(float(nation['infrastructure'])/nation['num_cities'],2)}</td>
                        % endif

                        <td>${nation['score']}</td>
                        <td>${nation['vmode']}</td>

                        % if (datetime.utcnow() - datetime.strptime(nation['last_active'], "%Y-%m-%d %H:%M:%S")).total_seconds()/3600 > 72:
                        <td style="color:red">${round((datetime.utcnow() - datetime.strptime(nation['last_active'], "%Y-%m-%d %H:%M:%S")).total_seconds()/3600)}</td>
                        % else:
                        <td>${round((datetime.utcnow() - datetime.strptime(nation['last_active'], "%Y-%m-%d %H:%M:%S")).total_seconds()/3600)}</td>
                        % endif

                        <td>${round(int(nation['soldiers'])/(nation['num_cities']*5*3000),2)}</td>
                        <td>${round(int(nation['tanks'])/(nation['num_cities']*5*250),2)}</td>
                        <td>${round(int(nation['aircraft'])/(nation['num_cities']*5*15),2)}</td>
                        <td>${round(int(nation['ships'])/(nation['num_cities']*3*5),2)}</td>

                        % if round(((int(nation['soldiers'])/(nation['num_cities']*5*3000)+int(nation['tanks'])/(nation['num_cities']*5*250)+int(nation['aircraft'])/(nation['num_cities']*5*15)+int(nation['ships'])/(nation['num_cities']*5*5))/4),2) <= 0.2:
                        <td style="color:red">${round(((int(nation['soldiers'])/(nation['num_cities']*5*3000)+int(nation['tanks'])/(nation['num_cities']*5*250)+int(nation['aircraft'])/(nation['num_cities']*5*15)+int(nation['ships'])/(nation['num_cities']*5*5))/4),2)}</td>
                        % else:
                        <td>${round(((int(nation['soldiers'])/(nation['num_cities']*5*3000)+int(nation['tanks'])/(nation['num_cities']*5*250)+int(nation['aircraft'])/(nation['num_cities']*5*15)+int(nation['ships'])/(nation['num_cities']*3*5))/4),2)}</td>
                        % endif

                        <td style="color:${nation['mmr_color']}">${nation['mmr']}</td>

                        % if nation['user_object']['audited']:
                        <td>${nation['user_object']['audited']}</td>
                        % else:
                        <td></td>
                        %endif

                        % for rs in ['al', 'ba', 'co', 'fo', 'ga', 'ir', 'le', 'mo', 'mu', 'oi', 'st', 'ur', 'total']:
                            % if nation['user_object'][rs] < 0:
                            <td style="color:red">${f"{round(nation['user_object'][rs]):,}"}</td>
                            % else:
                            <td>${f"{round(nation['user_object'][rs]):,}"}</td>
                            % endif
                        % endfor

                    </tr>

                    % endfor


            </table>
            <p>All cities: ${aa['cities']}, Total score: ${round(aa['score'],2)}, Total members: ${aa['members']}</p>
            <p>Last updated: ${timestamp} GMT<br><a href="http://www.timezoneconverter.com/cgi-bin/tzc.tzc" target="_blank">Timezone converter</a></p>
            <script>
                grid.onclick = function (e) {
                    if (e.target.tagName != 'TH') return;

                    let th = e.target;
                    // if TH, then sort
                    // cellIndex is the number of th:
                    //   0 for the first column
                    //   1 for the second column, etc
                    sortTable(th.cellIndex, th.dataset.type);
                };

                function sortTable(n, type) {
                    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                    table = document.getElementById("grid");
                    switching = true;
                    //Set the sorting direction to ascending:
                    dir = "asc";
                    /*Make a loop that will continue until
                    no switching has been done:*/
                    while (switching) {
                        //start by saying: no switching is done:
                        switching = false;
                        rows = table.rows;
                        /*Loop through all table rows (except the
                        first, which contains table headers):*/
                        for (i = 1; i < (rows.length - 1); i++) {
                            //start by saying there should be no switching:
                            shouldSwitch = false;
                            /*Get the two elements you want to compare,
                            one from current row and one from the next:*/
                            x = rows[i].getElementsByTagName("TD")[n];
                            y = rows[i + 1].getElementsByTagName("TD")[n];
                            /*check if the two rows should switch place,
                            based on the direction, asc or desc:*/
                            if (dir == "asc" && type == "string") {
                                if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                                    //if so, mark as a switch and break the loop:
                                    shouldSwitch = true;
                                    break;
                                }
                            } else if (dir == "desc" && type == "string") {
                                if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                                    //if so, mark as a switch and break the loop:
                                    shouldSwitch = true;
                                    break;
                                }
                            }

                            if (dir == "asc" && type == "number") {
                                if (parseFloat(x.innerHTML.replace(/,/g,"")) > parseFloat(y.innerHTML.replace(/,/g,""))) {
                                    //if so, mark as a switch and break the loop:
                                    shouldSwitch = true;
                                    break;
                                }
                            } else if (dir == "desc" && type == "number") {
                                if (parseFloat(x.innerHTML.replace(/,/g,"")) < parseFloat(y.innerHTML.replace(/,/g,""))) {
                                    //if so, mark as a switch and break the loop:
                                    shouldSwitch = true;
                                    break;
                                }
                            }
                        }


                        if (shouldSwitch) {
                            /*If a switch has been marked, make the switch
                            and mark that a switch has been done:*/
                            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                            switching = true;
                            //Each time a switch is done, increase this count by 1:
                            switchcount++;
                        } else {
                            /*If no switching has been done AND the direction is "asc",
                            set the direction to "desc" and run the while loop again.*/
                            if (switchcount == 0 && dir == "asc") {
                                dir = "desc";
                                switching = true;
                            }
                        }
                    }
                }
            </script>
        </div>
    </body>
    </html>
            """
            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': "{nations(page:1 first:500 alliance_id:4729){data{id alliance_id alliance_position leader_name nation_name color num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available cities{infrastructure barracks factory airforcebase drydock}}}}"}) as temp:
                church = (await temp.json())['data']['nations']['data']
            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={convent_key}', json={'query': "{nations(page:1 first:500 alliance_id:7531){data{id alliance_id alliance_position leader_name nation_name color num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available cities{infrastructure barracks factory airforcebase drydock}}}}"}) as temp:
                convent = (await temp.json())['data']['nations']['data']
            sum = church + convent

            nations = []

            for nation in sum:
                if nation['alliance_position'] != "APPLICANT":
                    nations.append(nation)


            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={convent_key}', json={'query': "{alliances(first:2 id:[4729,7531]){data{score nations{num_cities alliance_position}}}}"}) as temp:
                alliances = (await temp.json())['data']['alliances']['data']

            score = alliances[0]['score'] + alliances[1]['score']
            cities = 0
            for i in range(2):
                for nation in alliances[i-1]['nations']:
                    cities += nation['num_cities']

            aa = {"members": len(nations), "cities": cities, "score": score, "mmr": mongo.mmr.find_one({})}

            users = list(self.bot.get_all_members())
            rss = ['aluminum', 'bauxite', 'coal', 'food', 'gasoline', 'iron', 'lead', 'munitions', 'money', 'oil', 'steel', 'uranium']
            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': "{tradeprices(limit:1){coal oil uranium iron bauxite lead gasoline munitions steel aluminum food}}"}) as resp:
                prices = (await resp.json())['data']['tradeprices'][0]
                prices['money'] = 1
           
            for nation in nations:
                x = mongo.users.find_one({"nationid": str(nation['id'])})
                nation['user_object'] = {'discordid': '', 'username': '', "audited": ''}
                if x == None:
                    nation['user_object'].update({'discordid': '¯\_(ツ)_/¯', "username": '¯\_(ツ)_/¯'})
                else:
                    for user in users:
                        nation['user_object'].update({'discordid': x['user'], "audited": x['audited']})
                        if user.id == x['user']:
                            nation['user_object']['username'] = str(user)
                            break
                        else:
                            nation['user_object']['username'] = "¯\_(ツ)_/¯"
                y = mongo.total_balance.find_one({"nationid": str(nation['id'])})
                if y == None:
                    nation['user_object'].update({"total": 0, "al": 0, "ba": 0, "co": 0, "fo": 0, "ga": 0, "ir": 0, "le": 0, "mu": 0, "mo": 0, "oi": 0, "st": 0, "ur": 0})
                else:
                    con_total = 0
                    for rs in rss:
                        amount = y[rs[:2].lower()]
                        price = int(prices[rs])
                        con_total += amount * price
                    nation['user_object'].update({"total": round(con_total), "al": y['al'], "ba": y['ba'], "co": y['co'], "fo": y['fo'], "ga": y['ga'], "ir": y['ir'], "le": y['le'], "mu": y['mu'], "mo": y['mo'], "oi": y['oi'], "st": y['st'], "ur": y['ur']})
                nation['infrastructure'] = 0
                barracks = 0
                factories = 0
                hangars = 0
                drydocks = 0
                for city in nation['cities']:
                    nation['infrastructure'] += city['infrastructure']
                    barracks += city['barracks']
                    factories += city['factory']
                    hangars += city['airforcebase']
                    drydocks += city['drydock']
                nation['mmr'] = f"{round(barracks/nation['num_cities'],1)}/{round(factories/nation['num_cities'],1)}/{round(hangars/nation['num_cities'],1)}/{round(drydocks/nation['num_cities'],1)}"
                nation['mmr_color'] = "black"
                if barracks/nation['num_cities'] < aa['mmr']['bar'] or factories/nation['num_cities'] < aa['mmr']['fac'] or hangars/nation['num_cities'] < aa['mmr']['han'] or drydocks/nation['num_cities'] < aa['mmr']['dry']:
                    nation['mmr_color'] = "red"



            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')

            result = Template(template).render(aa=aa,nations=nations,timestamp=timestamp, datetime=datetime)

            mongo.sheet_code.replace_one({},{"code": result})
            
            print('webpage updated')


def setup(bot):
    bot.add_cog(Sheet(bot))